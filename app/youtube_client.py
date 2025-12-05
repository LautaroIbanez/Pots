import sys
import logging
import requests
import re
from typing import List, Optional
from urllib.parse import unquote
import isodate
from app.config import YOUTUBE_API_KEY, MAX_VIDEOS_PER_CHANNEL, MIN_VIDEO_DURATION_SECONDS, get_min_duration_for_channel
from app.models import VideoSummary

logger = logging.getLogger(__name__)

def log_print(*args, **kwargs):
    """Print que fuerza el flush para ver logs en tiempo real."""
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)
    print(*args, **kwargs)
    sys.stdout.flush()

def extract_channel_id_from_url(channel_url: str) -> Optional[str]:
    """Extract channel ID from various YouTube URL formats."""
    channel_id_match = re.search(r"channel/([a-zA-Z0-9_-]+)", channel_url)
    if channel_id_match:
        return channel_id_match.group(1)
    if "@" in channel_url:
        username = channel_url.split("@")[-1].split("/")[0].split("?")[0]
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(f"https://www.youtube.com/@{username}", allow_redirects=True, headers=headers, timeout=10)
            matches = re.findall(r'"channelId":"([^"]+)"', response.text)
            if matches:
                return matches[0]
            match = re.search(r'"externalId":"([^"]+)"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Error extracting channel ID from URL for @{username}: {e}")
    match = re.search(r"c/([^/?]+)", channel_url)
    if match:
        channel_handle = match.group(1)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(f"https://www.youtube.com/c/{channel_handle}", allow_redirects=True, headers=headers, timeout=10)
            matches = re.findall(r'"channelId":"([^"]+)"', response.text)
            if matches:
                return matches[0]
        except Exception as e:
            print(f"Error extracting channel ID from URL for c/{channel_handle}: {e}")
    return None

def get_channel_id(channel_url: str) -> Optional[str]:
    """Get channel ID using YouTube Data API."""
    if not YOUTUBE_API_KEY:
        return extract_channel_id_from_url(channel_url)
    channel_url_decoded = unquote(channel_url)
    channel_id_match = re.search(r"channel/([a-zA-Z0-9_-]+)", channel_url_decoded)
    if channel_id_match:
        return channel_id_match.group(1)
    username_match = re.search(r"@([^/?]+)", channel_url_decoded)
    if username_match:
        handle = username_match.group(1)
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={handle}&key={YOUTUBE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data["items"][0]["id"]
        except Exception as e:
            print(f"Error getting channel ID for handle {handle}: {e}")
        try:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={handle}&type=channel&maxResults=1&key={YOUTUBE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data["items"][0]["id"]["channelId"]
        except Exception as e:
            print(f"Error searching channel for {handle}: {e}")
    match = re.search(r"c/([^/?]+)", channel_url_decoded)
    if match:
        channel_handle = match.group(1)
        try:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={channel_handle}&type=channel&maxResults=1&key={YOUTUBE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data["items"][0]["id"]["channelId"]
        except Exception as e:
            pass
    return extract_channel_id_from_url(channel_url_decoded)

def get_channel_name(channel_id: str) -> str:
    """Get channel name from channel ID."""
    if not YOUTUBE_API_KEY:
        return "Unknown Channel"
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&key={YOUTUBE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                return data["items"][0]["snippet"]["title"]
    except Exception as e:
        print(f"Error getting channel name: {e}")
    return "Unknown Channel"

def get_latest_videos(channel_url: str, min_duration_seconds: int = None) -> List[VideoSummary]:
    """
    Get latest long videos from a YouTube channel, EXCLUYENDO Shorts y videos cortos.
    Usa el playlist de uploads del canal para obtener videos de la pestaña "Videos" con paginación.
    
    Args:
        channel_url: URL del canal de YouTube
        min_duration_seconds: Duración mínima en segundos (default: desde config por canal o global)
    """
    if min_duration_seconds is None:
        min_duration_seconds = get_min_duration_for_channel(channel_url)
    if not YOUTUBE_API_KEY:
        log_print(f"Warning: YOUTUBE_API_KEY not configured. Cannot fetch videos for {channel_url}")
        return []
    channel_id = get_channel_id(channel_url)
    if not channel_id:
        log_print(f"Could not get channel ID for {channel_url}")
        return []
    channel_name = get_channel_name(channel_id)
    duration_min = min_duration_seconds // 60
    duration_sec = min_duration_seconds % 60
    if duration_min > 0:
        duration_str = f"{duration_min}m{duration_sec}s" if duration_sec > 0 else f"{duration_min} minutos"
    else:
        duration_str = f"{duration_sec} segundos"
    log_print(f"  Buscando videos (mínimo {duration_str}) - EXCLUYENDO Shorts...")
    try:
        # 1) Obtener el playlist de uploads del canal
        channels_url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={YOUTUBE_API_KEY}"
        channels_response = requests.get(channels_url)
        if channels_response.status_code != 200:
            error_data = channels_response.json() if channels_response.content else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            log_print(f"Error fetching channel details for {channel_url} (status {channels_response.status_code}): {error_msg}")
            return []
        channels_data = channels_response.json()
        if not channels_data.get("items"):
            log_print(f"No channel data found for {channel_url}")
            return []
        uploads_playlist_id = channels_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        log_print(f"  Playlist de uploads encontrado: {uploads_playlist_id}")
        
        # 2) Recorrer el playlist de uploads con paginación
        video_ids = []
        next_page_token = None
        max_pages = 10  # Límite de seguridad para evitar loops infinitos
        page_count = 0
        
        while len(video_ids) < MAX_VIDEOS_PER_CHANNEL * 10 and page_count < max_pages:
            page_count += 1
            playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={uploads_playlist_id}&maxResults=50&key={YOUTUBE_API_KEY}"
            if next_page_token:
                playlist_url += f"&pageToken={next_page_token}"
            playlist_response = requests.get(playlist_url)
            if playlist_response.status_code != 200:
                error_data = playlist_response.json() if playlist_response.content else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                log_print(f"Error fetching playlist items (status {playlist_response.status_code}): {error_msg}")
                break
            playlist_data = playlist_response.json()
            page_video_ids = [item["contentDetails"]["videoId"] for item in playlist_data.get("items", [])]
            video_ids.extend(page_video_ids)
            log_print(f"  Página {page_count}: {len(page_video_ids)} videos encontrados (total acumulado: {len(video_ids)})")
            next_page_token = playlist_data.get("nextPageToken")
            if not next_page_token:
                break
        
        if not video_ids:
            log_print(f"  No se encontraron videos en el playlist de uploads")
            return []
        
        # 3) Obtener detalles de los videos (incluyendo duración) para filtrar Shorts
        # Procesar en lotes de 50 (límite de la API)
        long_videos = []
        batch_size = 50
        for i in range(0, len(video_ids), batch_size):
            batch_ids = video_ids[i:i + batch_size]
            video_ids_str = ",".join(batch_ids)
            details_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_ids_str}&key={YOUTUBE_API_KEY}"
            details_response = requests.get(details_url)
            if details_response.status_code != 200:
                log_print(f"Error fetching video details for batch {i // batch_size + 1}")
                continue
            details_data = details_response.json()
            
            for item in details_data.get("items", []):
                video_id = item["id"]
                snippet = item["snippet"]
                content_details = item.get("contentDetails", {})
                duration_iso = content_details.get("duration", "PT0S")
                
                # Parsear duración ISO 8601 usando isodate
                try:
                    duration = isodate.parse_duration(duration_iso).total_seconds()
                except Exception:
                    duration = 0
                
                duration_min = int(duration // 60)
                duration_sec = int(duration % 60)
                
                # FILTRAR SHORTS: solo videos más largos que min_duration_seconds
                if duration < min_duration_seconds:
                    log_print(f"  [FILTRADO] {snippet['title'][:50]}... - Duración: {duration_min}m{duration_sec}s (menor a {min_duration_seconds // 60}m{min_duration_seconds % 60}s, se excluye)")
                    continue
                
                log_print(f"  [✓ ACEPTADO] {snippet['title'][:60]}... - Duración: {duration_min}m{duration_sec}s - ID: {video_id}")
                
                video_summary = VideoSummary(
                    video_id=video_id,
                    title=snippet["title"],
                    channel_name=channel_name,
                    channel_url=channel_url,
                    published_at=snippet["publishedAt"],
                    video_url=f"https://www.youtube.com/watch?v={video_id}",
                    has_transcript=False
                )
                long_videos.append(video_summary)
                
                # Limitar a MAX_VIDEOS_PER_CHANNEL videos largos
                if len(long_videos) >= MAX_VIDEOS_PER_CHANNEL:
                    break
            
            if len(long_videos) >= MAX_VIDEOS_PER_CHANNEL:
                break
        
        log_print(f"  Total videos aceptados: {len(long_videos)} (videos < {min_duration_seconds // 60}m{min_duration_seconds % 60}s excluidos)")
        return long_videos
    except Exception as e:
        log_print(f"  ✗ Error getting videos for channel {channel_url}: {e}")
        import traceback
        traceback.print_exc()
        return []

