from pydantic import BaseModel
from typing import Optional
from enum import Enum


class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadRequest(BaseModel):
    url: str
    format: Optional[str] = "mp4"
    audio_only: Optional[bool] = False
    output_template: Optional[str] = "%(title)s.%(ext)s"
    video_format_id: Optional[str] = None  # yt-dlp format selector for video downloads
    title: Optional[str] = None  # 视频标题（前端传递）


class DownloadProgress(BaseModel):
    task_id: str
    status: DownloadStatus
    url: Optional[str] = None
    filename: Optional[str] = None
    title: Optional[str] = None  # 视频标题
    progress: float = 0.0
    stage: Optional[str] = None  # 当前阶段: extracting/info/thumbnail/downloading/merging/finalizing
    speed: Optional[str] = None
    eta: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[float] = None  # Unix timestamp


class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    created_at: float


class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    fps: Optional[float] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    format_note: Optional[str] = None


class VideoInfo(BaseModel):
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    formats: list[VideoFormat] = []