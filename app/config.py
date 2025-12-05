import os
import json
from dotenv import load_dotenv
from typing import Dict, Optional

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
# Duración mínima global (default: 120 segundos = 2 minutos para filtrar solo Shorts)
MIN_VIDEO_DURATION_SECONDS = int(os.getenv("MIN_VIDEO_DURATION_SECONDS", "120"))
DATA_DIR = "data"
SUMMARIES_FILE = os.path.join(DATA_DIR, "summaries.json")
CHANNEL_CONFIG_FILE = os.path.join(DATA_DIR, "channel_config.json")

# Configuración por canal: mapea URL del canal a duración mínima en segundos
# Si no se especifica, se usa MIN_VIDEO_DURATION_SECONDS global
CHANNEL_MIN_DURATION: Dict[str, int] = {}

def load_channel_config() -> Dict[str, int]:
    """Carga configuración por canal desde archivo JSON si existe."""
    config = {}
    if os.path.exists(CHANNEL_CONFIG_FILE):
        try:
            with open(CHANNEL_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Convertir valores a int
                    config = {k: int(v) for k, v in data.items() if isinstance(v, (int, str))}
        except Exception as e:
            print(f"Error loading channel config from {CHANNEL_CONFIG_FILE}: {e}")
    return config

def get_min_duration_for_channel(channel_url: str) -> int:
    """Obtiene la duración mínima configurada para un canal específico."""
    # Cargar configuración desde archivo
    channel_config = load_channel_config()
    # Combinar con configuración hardcodeada (tiene prioridad)
    all_config = {**channel_config, **CHANNEL_MIN_DURATION}
    # Retornar valor por canal o global
    return all_config.get(channel_url, MIN_VIDEO_DURATION_SECONDS)

# Cargar configuración inicial
CHANNEL_MIN_DURATION.update(load_channel_config())

