from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models.schemas import FileInfo
from app.models.database import DownloadedFileModel, get_db
from app.config import DOWNLOAD_DIR
from pathlib import Path
from app.logger import app_logger
from app.services.downloader import get_file_group_key, remove_downloaded_file_from_db

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/", response_model=list[FileInfo])
async def list_files():
    """从数据库读取文件列表（不扫描文件系统，提升速度）"""
    db = next(get_db())
    try:
        records = db.query(DownloadedFileModel).order_by(
            DownloadedFileModel.created_at.desc()
        ).all()
        
        files = []
        for r in records:
            file_path = DOWNLOAD_DIR / r.name
            if file_path.exists():
                files.append(FileInfo(
                    name=r.name,
                    path=r.path,
                    size=file_path.stat().st_size,
                    created_at=r.created_at.timestamp()
                ))
            else:
                # 文件已被删除，清理 DB 记录
                db.delete(r)
                db.commit()
        
        return files
    finally:
        db.close()


@router.get("/{filename}")
async def download_file(filename: str):
    file_path = DOWNLOAD_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.delete("/{filename}")
async def delete_file(filename: str):
    file_path = DOWNLOAD_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # 根据文件类型决定删除策略
    ext = Path(filename).suffix.lower()
    video_exts = ('.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv')
    
    if ext in video_exts:
        # 视频文件：删除同组所有文件（缩略图、info.json、nfo 等）
        group_key = get_file_group_key(filename)
        deleted_files = []
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file() and get_file_group_key(f.name) == group_key:
                try:
                    f.unlink()
                    deleted_files.append(f.name)
                    app_logger.debug(f"Deleted companion file: {f.name}")
                except Exception as e:
                    app_logger.warning(f"Failed to delete {f.name}: {e}")
                # 清理 DB 记录
                remove_downloaded_file_from_db(f.name)
        return {"message": "File deleted", "deleted": deleted_files}
    else:
        # 非视频文件：只删自身
        file_path.unlink()
        remove_downloaded_file_from_db(filename)
        return {"message": "File deleted", "deleted": [filename]}
