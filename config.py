import os

API_ID = os.getenv("API_ID", "21740783")
API_HASH = os.getenv("API_HASH", "a5dc7fec8302615f5b441ec5e238cd46")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7116266807:AAFiuS4MxcubBiHRyzKEDnmYPCRiS0f3aGU")

# Directory to save and process files
SAVE_DIR = './downloads'

# FFmpeg path (if FFmpeg is not in your PATH, specify the full path here)
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# AI model settings
MODEL_NAME = "facebook/bart-large-mnli"

