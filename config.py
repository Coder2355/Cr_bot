import os

API_ID = os.getenv("API_ID", "21740783")
API_HASH = os.getenv("API_HASH", "a5dc7fec8302615f5b441ec5e238cd46")
BOT_TOKEN = os.getenv("BOT_TOKEN", "6610201435:AAHEv2YoM2ZEtlEdqjilv9mZGjT9Uzzrntw")

# Directory to save and process files
SAVE_DIR = './downloads'


# Path to your watermark image file
WATERMARK_PATH = "watermark.png"  # The watermark image created by the bot

# Directory for storing temporary video files
WORKING_DIR = "downloads"  # Directory for saving downloaded and processed files

# AI model settings
MODEL_NAME = "facebook/bart-large-mnli"

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "/usr/bin/ffmpeg")  # Default location of FFmpeg

# config.py

# Crunchyroll Premium Credentials
CRUNCHYROLL_USERNAME = 'http://segunblaksley@live.com'
CRUNCHYROLL_PASSWORD = '123456789'
