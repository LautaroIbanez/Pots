import json
import os
from datetime import datetime
from typing import Dict, Optional
from app.config import DATA_DIR, SUMMARIES_FILE
from app.models import VideoSummary

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_summaries() -> Dict[str, dict]:
    """Load summaries from JSON file."""
    ensure_data_dir()
    if not os.path.exists(SUMMARIES_FILE):
        return {}
    try:
        with open(SUMMARIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading summaries: {e}")
        return {}

def save_summaries(summaries: Dict[str, dict]):
    """Save summaries to JSON file."""
    ensure_data_dir()
    try:
        with open(SUMMARIES_FILE, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving summaries: {e}")

def get_cached_summary(video_id: str) -> Optional[VideoSummary]:
    """Get cached summary for a video."""
    summaries = load_summaries()
    if video_id in summaries:
        data = summaries[video_id]
        return VideoSummary(**data)
    return None

def save_summary(video_summary: VideoSummary):
    """Save or update a video summary."""
    summaries = load_summaries()
    summaries[video_summary.video_id] = {
        "video_id": video_summary.video_id,
        "title": video_summary.title,
        "channel_name": video_summary.channel_name,
        "channel_url": video_summary.channel_url,
        "published_at": video_summary.published_at,
        "video_url": video_summary.video_url,
        "summary": video_summary.summary,
        "has_transcript": video_summary.has_transcript,
        "generated_at": video_summary.generated_at or datetime.now().isoformat()
    }
    save_summaries(summaries)

def get_all_summaries() -> list[VideoSummary]:
    """Get all cached summaries."""
    summaries = load_summaries()
    return [VideoSummary(**data) for data in summaries.values()]

