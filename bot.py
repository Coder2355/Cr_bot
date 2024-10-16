import os
import ffmpeg
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
import time

# Load configuration from config.py
from config import API_ID, API_HASH, BOT_TOKEN

bot = Client("video_audio_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to show progress for downloads/uploads
async def progress_bar(current, total, message, status):
    try:
        percent = current * 100 / total
        progress_message = f"{status}: {percent:.1f}%\n{current / 1024 / 1024:.1f}MB of {total / 1024 / 1024:.1f}MB"
        await message.edit(progress_message)
    except MessageNotModified:
        pass

@bot.on_message(filters.command(["merge_video_audio"]) & filters.reply)
async def merge_video_audio(client, message):
    if not message.reply_to_message:
        await message.reply("Please reply to a video file with this command.")
        return

    video_msg = message.reply_to_message
    if not video_msg.video and not video_msg.document:
        await message.reply("Please reply to a video file.")
        return

    # Ask the user to upload the audio file
    await message.reply("Please upload the audio file to merge with the video.")

    # Wait for the user to upload the audio file
    response = await client.listen(message.chat.id, filters=filters.audio | filters.document)

    audio_msg = response
    if not audio_msg.audio and not audio_msg.document:
        await message.reply("Please upload a valid audio file.")
        return

    # Download the video file with a progress bar
    video_progress = await message.reply("Downloading video...")
    video_file = await video_msg.download(progress=lambda current, total: asyncio.run(progress_bar(current, total, video_progress, "Downloading video")))

    # Download the audio file with a progress bar
    audio_progress = await message.reply("Downloading audio...")
    audio_file = await audio_msg.download(progress=lambda current, total: asyncio.run(progress_bar(current, total, audio_progress, "Downloading audio")))

    # Ask the user for a new name for the output file
    await message.reply("Please provide a new name for the merged video (without the extension).")

    # Wait for the user's response with the new name
    new_name_msg = await client.listen(message.chat.id, filters=filters.text)
    new_name = new_name_msg.text.strip()

    if not new_name:
        await message.reply("Invalid name. Merging process aborted.")
        return

    # Set the output file name with the new name provided by the user
    output_file = f"{new_name}.mp4"

    # FFmpeg command to remove existing audio from the video and add the new audio
    try:
        await message.reply("Merging video and audio...")

        # Merge video with the new audio
        ffmpeg.input(video_file).output(output_file, codec="copy", shortest=None, map="0:v:0", map="1:a:0").run()

        await message.reply(f"Merging complete. The file has been renamed to {new_name}. Uploading the file...")

        # Upload the merged file with a progress bar
        upload_progress = await message.reply("Uploading file...")
        await message.reply_document(
            document=output_file,
            progress=lambda current, total: asyncio.run(progress_bar(current, total, upload_progress, "Uploading file"))
        )

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

    finally:
        # Clean up
        os.remove(video_file)
        os.remove(audio_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    bot.run()
