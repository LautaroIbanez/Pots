import sys
import time
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from typing import Optional

from app.config import (
    TRANSCRIPT_MAX_RETRIES,
    TRANSCRIPT_RETRY_BACKOFF_SECONDS,
    TRANSCRIPT_REQUEST_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)

def log_print(*args, **kwargs):
    """Print que fuerza el flush para ver logs en tiempo real."""
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)
    print(*args, **kwargs)
    sys.stdout.flush()

def get_video_transcript(video_id: str) -> Optional[str]:
    """
    Devuelve el transcript como texto plano (una sola string),
    o None si realmente no hay forma de obtenerlo.
    Intenta múltiples variantes de español y también inglés con traducción.
    Incluye reintentos con backoff ante errores transitorios (p. ej. 429).
    """
    last_error = None
    for attempt in range(1, TRANSCRIPT_MAX_RETRIES + 1):
        if TRANSCRIPT_REQUEST_DELAY_SECONDS > 0:
            time.sleep(TRANSCRIPT_REQUEST_DELAY_SECONDS)

        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript_obj = None
            available_langs = [t.language_code for t in list(transcripts)]
            log_print(
                f"      Idiomas disponibles para {video_id}: {', '.join(available_langs) if available_langs else 'ninguno'}"
            )

            # 1) Intentar en español (varias variantes) - preferir manuales
            preferred_langs = ['es', 'es-419', 'es-ES', 'es-MX', 'es-AR']
            try:
                transcript_obj = transcripts.find_manually_created_transcript(preferred_langs)
                log_print("      ✓ Transcript manual en español encontrado")
            except NoTranscriptFound:
                try:
                    # Si no hay manual, intentar generadas automáticamente
                    transcript_obj = transcripts.find_generated_transcript(preferred_langs)
                    log_print("      ✓ Transcript generado en español encontrado")
                except NoTranscriptFound:
                    # 2) Probar en inglés y traducir a español
                    try:
                        en_transcript = transcripts.find_transcript(['en'])
                        transcript_obj = en_transcript.translate('es')
                        log_print("      ✓ Transcript en inglés encontrado y traducido a español")
                    except NoTranscriptFound:
                        # 3) Último intento: cualquier idioma disponible y traducir a español
                        try:
                            available = list(transcripts)
                            if available:
                                first_transcript = available[0]
                                transcript_obj = first_transcript.translate('es')
                                log_print(
                                    f"      ✓ Transcript en {first_transcript.language_code} encontrado y traducido a español"
                                )
                        except (NoTranscriptFound, Exception) as e:
                            log_print(f"      ✗ No se pudo obtener transcript (último intento falló: {e})")
                            return None

            if transcript_obj:
                chunks = transcript_obj.fetch()
                text = " ".join(chunk["text"] for chunk in chunks)
                return text.strip() or None

            return None

        except TranscriptsDisabled:
            log_print(f"      ✗ Transcripts deshabilitados para {video_id}")
            return None
        except NoTranscriptFound:
            log_print(f"      ✗ No se encontró transcript para {video_id}")
            return None
        except VideoUnavailable:
            log_print(f"      ✗ Video no disponible: {video_id}")
            return None
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["too many requests", "429", "rate limit"]):
                if attempt < TRANSCRIPT_MAX_RETRIES:
                    wait_time = TRANSCRIPT_RETRY_BACKOFF_SECONDS * attempt
                    log_print(
                        f"      ⚠️ 429/Rate limit para {video_id}; reintentando en {wait_time}s (intento {attempt}/{TRANSCRIPT_MAX_RETRIES})"
                    )
                    time.sleep(wait_time)
                    continue
                log_print(f"      ✗ Demasiados intentos para {video_id} (429 Too Many Requests)")
                return None
            if any(keyword in error_msg for keyword in ["no element found", "parse", "xml", "malformed", "invalid"]):
                log_print(f"      ✗ Error de parsing para {video_id}: {error_msg[:100]}")
                return None
            log_print(f"      ✗ Error inesperado para {video_id}: {e}")
            return None

    if last_error:
        log_print(f"      ✗ No se pudo obtener transcript para {video_id}: {last_error}")
    return None

