import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
API_ID = os.getenv("API_ID", "4857766")
API_HASH = os.getenv("API_HASH", "6c3c6facf5598a4b318e138f8c407028")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7936596591:AAER2UobMr44zDa1lrUxcQfDgnHaPL8mHZI")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://hello:hello@cluster0.vc2htx0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "ytdl_bot_db")
ADMINS = list(map(int, os.getenv("ADMINS", "7361945688").split()))

# List of additional IDs to add
ADDITIONAL_IDS = [1596559467]  # Add as many as needed

# Extend the ADMINS list with additional IDs
ADMINS.extend(ADDITIONAL_IDS)

# Remove duplicates (if any) and ensure it's a list
ADMINS = list(set(ADMINS))
#ADMINS = list(map(int, os.getenv("ADMINS", "7361945688, 1596559467").split()))
PAID_USERS = list(map(int, os.getenv("PAID_USERS", "7361945688").split()))

# Default Settings
DEFAULT_UPLOAD_MODE = "video"  # 'video' or 'file'
DEFAULT_SPLIT_SETTING = True   # Split files larger than 1.95GB
DEFAULT_THUMBNAIL_GENERATION = True  # Generate thumbnail from video
DEFAULT_CAPTION_ENABLED = False  # Custom caption
DEFAULT_GENERATE_SCREENSHOTS = False  # Generate screenshots after upload
DEFAULT_SAMPLE_VIDEO = False  # Generate sample video

# YT-DLP Default Settings
DEFAULT_FORMAT = "bestvideo+bestaudio"  # Default format

# Contact Information
CONTACT_ADMIN = "@NitinSahay for paid subscription"

# File Size Limits (in bytes)
MAX_FILE_SIZE = int(1.75 * (1024 ** 3))# 1.75GB

#free users tasks
TASKS = 20

# Temporary Download Path
DOWNLOAD_PATH = "./downloads/"
