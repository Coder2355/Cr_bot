import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, BOT_TOKEN
import ffmpeg

bot = Client("video_editor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store videos for merging
video_merger_dict = {}
bot_data = {}

# Start message
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome to the Video Editor Bot. You can send a video or document, and choose to trim or merge it.")

# When a video or document is sent, reply with Trim and Merge buttons
@bot.on_message(filters.video | filters.document)
async def video_handler(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is waiting for the second video for merging
    if user_id in video_merger_dict and video_merger_dict[user_id]["awaiting_second_video"]:
        await merge_video_process(client, message, user_id)
    else:
        # Show action buttons if this is the first video
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Trim Video", callback_data="trim_video")],
                [InlineKeyboardButton("Merge Video", callback_data="merge_video")]
            ]
        )
        # Store the original video message for later use (in case of merging)
        bot_data[user_id] = {"video_message": message}
        await message.reply("Choose an action for this video:", reply_markup=buttons)

# Handle callback for trim video
@bot.on_callback_query(filters.regex("trim_video"))
async def trim_video_callback(client, callback_query):
    await callback_query.message.reply("Please provide the start and end times (in seconds) to trim the video.\nExample: `10 60` to trim from 10s to 60s.")
    bot_data[callback_query.from_user.id]["action"] = "trim"

# Handle callback for merge video
@bot.on_callback_query(filters.regex("merge_video"))
async def merge_video_callback(client, callback_query):
    user_id = callback_query.from_user.id
    
    # Retrieve the original message containing the first video
    if user_id in bot_data and "video_message" in bot_data[user_id]:
        first_video_message = bot_data[user_id]["video_message"]
        first_video_path = await first_video_message.download()
        
        # Store the first video and mark waiting for the second video
        video_merger_dict[user_id] = {
            "first_video": first_video_path,
            "awaiting_second_video": True
        }
        await callback_query.message.reply("Please send the second video to merge.")
    else:
        await callback_query.message.reply("Error: Could not find the first video.")

# Trim the video
@bot.on_message(filters.text & filters.reply)
async def trim_video(client, message):
    user_id = message.from_user.id
    if user_id in bot_data and bot_data[user_id]["action"] == "trim":
        try:
            start_time, end_time = map(int, message.text.split())
            video = bot_data[user_id]["video_message"].video or bot_data[user_id]["video_message"].document

            # Status message for downloading
            download_message = await message.reply("Downloading the video...")
            file_path = await bot_data[user_id]["video_message"].download()
            await download_message.edit("Download complete. Trimming the video...")

            output_file = f"trimmed_{os.path.basename(file_path)}"

            # FFmpeg command for trimming
            ffmpeg.input(file_path, ss=start_time, to=end_time).output(output_file).run()

            # Status message for uploading
            await message.reply_video(output_file, caption="Here is your trimmed video.")
            os.remove(file_path)
            os.remove(output_file)

        except Exception as e:
            await message.reply(f"Error trimming video: {e}")

# Optimized Merge Process
async def merge_video_process(client, message, user_id):
    try:
        first_video_path = video_merger_dict[user_id]["first_video"]

        # Status message for downloading second video
        download_message = await message.reply("Downloading the second video...")
        second_video_path = await message.download()
        await download_message.edit("Second video downloaded. Merging the videos...")

        # Check if the two videos have the same codec, resolution, and frame rate
        first_video_info = ffmpeg.probe(first_video_path)
        second_video_info = ffmpeg.probe(second_video_path)

        first_video_stream = next(stream for stream in first_video_info['streams'] if stream['codec_type'] == 'video')
        second_video_stream = next(stream for stream in second_video_info['streams'] if stream['codec_type'] == 'video')

        if (first_video_stream['codec_name'] == second_video_stream['codec_name'] and
            first_video_stream['width'] == second_video_stream['width'] and
            first_video_stream['height'] == second_video_stream['height'] and
            first_video_stream['r_frame_rate'] == second_video_stream['r_frame_rate']):
            
            # Fast merging using concat demuxer (no re-encoding)
            with open("videos_to_merge.txt", "w") as f:
                f.write(f"file '{first_video_path}'\n")
                f.write(f"file '{second_video_path}'\n")
            
            output_file = f"merged_{os.path.basename(first_video_path)}"
            await asyncio.create_subprocess_exec("ffmpeg", "-f", "concat", "-safe", "0", "-i", "videos_to_merge.txt", "-c", "copy", output_file)
            
            # Status message for uploading
            await message.reply_video(output_file, caption="Here is your merged video.")
        
        else:
            # Fallback to re-encoding if videos differ in codec/resolution/frame rate
            temp_first = "reencoded_first.mp4"
            temp_second = "reencoded_second.mp4"

            # Re-encode the first video
            ffmpeg.input(first_video_path).output(temp_first, vcodec="libx264", acodec="aac", vf="scale=1280:720", r=30).run()
            
            # Re-encode the second video
            ffmpeg.input(second_video_path).output(temp_second, vcodec="libx264", acodec="aac", vf="scale=1280:720", r=30).run()

            output_file = f"merged_{os.path.basename(first_video_path)}"

            # Merge the re-encoded videos
            ffmpeg.concat(ffmpeg.input(temp_first), ffmpeg.input(temp_second), v=1, a=1).output(output_file).run()

            # Status message for uploading
            await message.reply_video(output_file, caption="Here is your merged video.")
            os.remove(temp_first)
            os.remove(temp_second)

        # Remove original files and temp files
        os.remove(first_video_path)
        os.remove(second_video_path)
        os.remove(output_file)

        # Clear the user from the dictionary
        del video_merger_dict[user_id]

    except Exception as e:
        await message.reply(f"Error merging videos: {e}")
        del video_merger_dict[user_id]

if __name__ == "__main__":
    bot.run()
