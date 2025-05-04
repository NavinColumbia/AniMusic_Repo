from pydantic import BaseModel
from typing import List

class AniListProfileIn(BaseModel):
    anilist_username: str
    mal_ids: List[int]

class FeedbackCreate(BaseModel):
    anilist_username: str
    song_id: str
    recommended_by: str
    watch_time: float
    total_video_time: float
    liked: bool

class VideoItem(BaseModel):
    youtube_video_id: str
    youtube_url: str
    song: str | None = None         
    anime: str | None = None        
    recommended_by: str


class PlaylistResponse(BaseModel):
    videos: List[VideoItem]
