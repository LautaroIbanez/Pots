from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VideoSummary(BaseModel):
    video_id: str
    title: str
    channel_name: str
    channel_url: str
    published_at: str
    video_url: str
    summary: Optional[str] = None
    has_transcript: bool = False
    generated_at: Optional[str] = None

class ChannelVideos(BaseModel):
    channel_name: str
    channel_url: str
    videos: list[VideoSummary]

