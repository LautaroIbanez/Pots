import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from app.config import YOUTUBE_CHANNEL_URLS, YOUTUBE_API_KEY
from app.youtube_client import get_latest_videos
from app.transcript_client import get_video_transcript
from app.summarizer import summarize_transcript
from app.storage import get_cached_summary, save_summary, get_all_summaries

# Configurar logging para que se vea en uvicorn
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_print(*args, **kwargs):
    """Print que fuerza el flush para ver logs en tiempo real."""
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)
    print(*args, **kwargs)
    sys.stdout.flush()

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/summaries")
async def get_summaries():
    """Get all cached summaries."""
    summaries = get_all_summaries()
    summaries_dict = {}
    for summary in summaries:
        channel_url = summary.channel_url
        if channel_url not in summaries_dict:
            summaries_dict[channel_url] = {
                "channel_name": summary.channel_name,
                "channel_url": channel_url,
                "videos": []
            }
        summaries_dict[channel_url]["videos"].append(summary.dict())
    result = [{"channel_name": v["channel_name"], "channel_url": v["channel_url"], "videos": v["videos"]} for v in summaries_dict.values()]
    return JSONResponse(content=result)

@app.post("/refresh")
async def refresh_summaries():
    """Refresh summaries by fetching latest videos and generating summaries."""
    # Validación temprana: verificar que YOUTUBE_API_KEY esté configurada
    if not YOUTUBE_API_KEY:
        error_msg = (
            "❌ ERROR: YOUTUBE_API_KEY no está configurada.\n\n"
            "Para usar esta aplicación, necesitas configurar tu API key de YouTube:\n"
            "1. Crea un archivo .env en la raíz del proyecto\n"
            "2. Agrega la línea: YOUTUBE_API_KEY=tu_api_key_aqui\n"
            "3. Obtén tu API key en: https://console.cloud.google.com/apis/credentials\n\n"
            "Sin la API key, no es posible obtener videos de YouTube."
        )
        log_print("\n" + "="*80)
        log_print(error_msg)
        log_print("="*80 + "\n")
        logger.error(error_msg)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "YOUTUBE_API_KEY no configurada",
                "message": "La API key de YouTube no está configurada. Por favor, configura YOUTUBE_API_KEY en tu archivo .env",
                "instructions": "1. Crea un archivo .env en la raíz del proyecto\n2. Agrega: YOUTUBE_API_KEY=tu_api_key_aqui\n3. Obtén tu API key en: https://console.cloud.google.com/apis/credentials"
            }
        )
    
    logger.info("="*80)
    logger.info("🔄 INICIANDO REFRESH - Buscando videos largos (EXCLUYENDO Shorts)")
    logger.info("="*80)
    log_print("\n" + "="*80)
    log_print("🔄 INICIANDO REFRESH - Buscando videos largos (EXCLUYENDO Shorts)")
    log_print("="*80)
    all_videos = []
    for channel_url in YOUTUBE_CHANNEL_URLS:
        try:
            log_print(f"\nProcesando canal: {channel_url}")
            videos = get_latest_videos(channel_url)
            log_print(f"  Videos encontrados: {len(videos)}")
            for video in videos:
                cached = get_cached_summary(video.video_id)
                if cached and cached.summary:
                    video.summary = cached.summary
                    video.has_transcript = cached.has_transcript
                    video.generated_at = cached.generated_at
                    log_print(f"  [CACHE] Video ya procesado: {video.title[:60]}...")
                else:
                    log_print(f"  Procesando video: {video.title[:60]}... (ID: {video.video_id})")
                    transcript = get_video_transcript(video.video_id)
                    if transcript:
                        log_print(f"    ✓ Transcript obtenido ({len(transcript)} caracteres)")
                        video.has_transcript = True
                        try:
                            summary_text = summarize_transcript(transcript, video.title, video.channel_name)
                            if summary_text and not summary_text.startswith("Error"):
                                video.summary = summary_text
                                log_print(f"    ✓ Resumen generado exitosamente")
                            else:
                                video.summary = "Hubo un error generando el resumen."
                                log_print(f"    ✗ Error en el resumen")
                        except Exception as e:
                            log_print(f"    ✗ Error generating summary: {e}")
                            video.summary = "Hubo un error generando el resumen."
                        video.generated_at = datetime.now().isoformat()
                    else:
                        log_print(f"    ✗ No se pudo obtener transcript para {video.video_id}")
                        video.has_transcript = False
                        video.summary = "No hay transcripción disponible para este video."
                    save_summary(video)
                all_videos.append(video)
        except Exception as e:
            log_print(f"Error processing channel {channel_url}: {e}")
            import traceback
            traceback.print_exc()
            continue
    summaries_dict = {}
    for video in all_videos:
        channel_url = video.channel_url
        if channel_url not in summaries_dict:
            summaries_dict[channel_url] = {
                "channel_name": video.channel_name,
                "channel_url": channel_url,
                "videos": []
            }
        summaries_dict[channel_url]["videos"].append(video.dict())
    result = [{"channel_name": v["channel_name"], "channel_url": v["channel_url"], "videos": v["videos"]} for v in summaries_dict.values()]
    log_print("="*80)
    log_print(f"✅ REFRESH COMPLETADO - Total videos procesados: {len(all_videos)}")
    log_print("="*80 + "\n")
    return JSONResponse(content=result)

