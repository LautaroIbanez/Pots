import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

YOUTUBE_CHANNEL_URLS = [
    "https://www.youtube.com/@RavaBursatil",
    "https://www.youtube.com/@Daniel_Pesalovo",
    "https://www.youtube.com/@somosbullmarket",
    "https://www.youtube.com/@JoseLuisCavatv",
    "https://www.youtube.com/@ClaveBursatilTV",
    "https://www.youtube.com/c/Jos%C3%A9LuisC%C3%A1rpatos",
    "https://www.youtube.com/@leanzicca",
    "https://www.youtube.com/@MundoDinerovideos",
    "https://www.youtube.com/@salvador.distefano",
]

MAX_VIDEOS_PER_CHANNEL = 3
MIN_VIDEO_DURATION_SECONDS = 600  # 10 minutos - filtra Shorts y videos cortos
DATA_DIR = "data"
SUMMARIES_FILE = os.path.join(DATA_DIR, "summaries.json")

