from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List

from app.config_manager import (
    load_config, get_ytdlp_current_version, download_ytdlp,
    save_cookies, delete_cookies, get_cookies_files
)
from app.logger import app_logger

router = APIRouter()

class ConfigResponse(BaseModel):
    default_format: str
    ytdlp_version: str
    ytdlp_current_version: str
    cookies_enabled: bool
    log_level: str
    language: str

class ConfigUpdate(BaseModel):
    default_format: str = None
    ytdlp_version: str = None
    cookies_enabled: bool = None
    log_level: str = None
    language: str = None

class UpdateResponse(BaseModel):
    success: bool
    version: str = None
    type: str = None
    error: str = None
    path: str = None

class CookiesUploadResponse(BaseModel):
    success: bool
    filename: str = None
    error: str = None

class CookiesFileItem(BaseModel):
    name: str
    size: int
    modified: float

@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    config = load_config()
    current_ytdlp_version = get_ytdlp_current_version()
    return ConfigResponse(
        default_format=config.default_format,
        ytdlp_version=config.ytdlp_version,
        ytdlp_current_version=current_ytdlp_version,
        cookies_enabled=config.cookies_enabled,
        log_level=config.log_level,
        language=config.language
    )

@router.put("/config", response_model=ConfigResponse)
async def update_config(config_update: ConfigUpdate):
    """Update configuration"""
    app_logger.info("="*60)
    app_logger.info("API: PUT /config")
    app_logger.info(f"Config update request: {config_update}")
    app_logger.info("="*60)
    
    try:
        config = load_config()
        app_logger.info(f"Current config loaded: {config}")
        
        has_changes = False
        
        if config_update.default_format is not None:
            if config_update.default_format not in ["mp4", "mkv"]:
                raise HTTPException(status_code=400, detail="Format must be mp4 or mkv")
            if config_update.default_format != config.default_format:
                config.default_format = config_update.default_format
                has_changes = True
                app_logger.info(f"Updated default_format: {config.default_format}")
        
        if config_update.ytdlp_version is not None:
            if config_update.ytdlp_version not in ["stable", "nightly"]:
                raise HTTPException(status_code=400, detail="Version must be 'stable' or 'nightly'")
            if config_update.ytdlp_version != config.ytdlp_version:
                config.ytdlp_version = config_update.ytdlp_version
                has_changes = True
                app_logger.info(f"Updated ytdlp_version: {config.ytdlp_version}")
        
        if config_update.cookies_enabled is not None:
            if config_update.cookies_enabled != config.cookies_enabled:
                config.cookies_enabled = config_update.cookies_enabled
                has_changes = True
                app_logger.info(f"Updated cookies_enabled: {config.cookies_enabled}")
        
        if config_update.log_level is not None:
            if config_update.log_level not in ["debug", "verbose", "info", "warn", "error"]:
                raise HTTPException(status_code=400, detail="Log level must be 'debug', 'verbose', 'info', 'warn', or 'error'")
            if config_update.log_level != config.log_level:
                config.log_level = config_update.log_level
                has_changes = True
                app_logger.info(f"Updated log_level: {config.log_level}")
                # 重新配置日志系统
                app_logger.setup_logger()
        
        if config_update.language is not None:
            if config_update.language not in ["en", "zh"]:
                raise HTTPException(status_code=400, detail="Language must be 'en' or 'zh'")
            if config_update.language != config.language:
                config.language = config_update.language
                has_changes = True
                app_logger.info(f"Updated language: {config.language}")
        
        if has_changes:
            from app.config_manager import save_config
            app_logger.info("Saving config...")
            save_config(config)
            app_logger.info("Config saved successfully")
        else:
            app_logger.info("No changes to save")
        
        current_ytdlp_version = get_ytdlp_current_version()
        result = ConfigResponse(
            default_format=config.default_format,
            ytdlp_version=config.ytdlp_version,
            ytdlp_current_version=current_ytdlp_version,
            cookies_enabled=config.cookies_enabled,
            log_level=config.log_level,
            language=config.language
        )
        app_logger.info(f"Returning config: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Failed to update config: {e}")
        app_logger.exception("Config update exception details:")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

@router.post("/config/ytdlp-update", response_model=UpdateResponse)
async def update_ytdlp_version():
    """Download/update yt-dlp executable to the configured version"""
    result = download_ytdlp()
    return UpdateResponse(**result)

@router.get("/config/cookies", response_model=List[CookiesFileItem])
async def list_cookies_files():
    """List all cookies files"""
    files = get_cookies_files()
    return [CookiesFileItem(name=f["name"], size=f["size"], modified=f["modified"]) for f in files]

@router.post("/config/cookies", response_model=CookiesUploadResponse)
async def upload_cookies(file: UploadFile = File(...)):
    """Upload a cookies file"""
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    content = await file.read()
    result = save_cookies(file.filename, content)
    
    return CookiesUploadResponse(**result)

@router.delete("/config/cookies/{filename}", response_model=dict)
async def remove_cookies(filename: str):
    """Delete a specific cookies file"""
    result = delete_cookies(filename)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "File not found"))
    return {"success": True}

class LogFileItem(BaseModel):
    name: str
    size: int
    modified: float
    date: str

@router.get("/config/logs", response_model=List[LogFileItem])
async def list_log_files():
    """List all log files grouped by date"""
    from app.config_manager import get_logs_dir
    import os
    
    logs_dir = get_logs_dir()
    files = []
    
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    # 从文件名提取日期：app_YYYYMMDD_HHMMSS.log
                    date_str = filename.split('_')[1] if '_' in filename else ''
                    files.append(LogFileItem(
                        name=filename,
                        size=stat.st_size,
                        modified=stat.st_mtime,
                        date=date_str
                    ))
    
    # 按修改时间倒序排列
    files.sort(key=lambda x: x.modified, reverse=True)
    return files

@router.get("/config/logs/{filename}")
async def get_log_file(filename: str):
    """Get content of a specific log file"""
    from app.config_manager import get_logs_dir
    import os
    
    logs_dir = get_logs_dir()
    filepath = os.path.join(logs_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {"filename": filename, "content": content}

@router.delete("/config/logs/{filename}", response_model=dict)
async def delete_log_file(filename: str):
    """Delete a specific log file"""
    from app.config_manager import get_logs_dir
    from app.logger import app_logger
    import os
    
    logs_dir = get_logs_dir()
    filepath = os.path.join(logs_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    # Check if this is the current log file being written to
    is_current_log = False
    if app_logger.file_handler:
        current_log_path = app_logger.file_handler.baseFilename
        # Compare just the filenames, not full paths (in case of path differences)
        if os.path.basename(current_log_path) == filename:
            is_current_log = True
    
    if is_current_log:
        # Close current log file before deleting
        app_logger.close_file()
        # Make sure file exists before deleting
        if os.path.exists(filepath):
            os.remove(filepath)
        # Reopen a new log file
        app_logger.reopen_file()
    else:
        os.remove(filepath)
        # Ensure logger is still active
        if not app_logger.file_handler:
            app_logger.reopen_file()
    
    # Log after reopening to ensure log goes to new file
    app_logger.info(f"Deleted log file: {filename}")
    return {"success": True}

@router.delete("/config/logs", response_model=dict)
async def clear_all_logs():
    """Delete all log files"""
    from app.config_manager import get_logs_dir
    from app.logger import app_logger
    import os
    
    logs_dir = get_logs_dir()
    deleted_count = 0
    
    # Close the current log file handler before deleting
    app_logger.close_file()
    
    try:
        if os.path.exists(logs_dir):
            for filename in os.listdir(logs_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(logs_dir, filename)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        deleted_count += 1
    finally:
        # Reopen a new log file after deletion
        app_logger.reopen_file()
    
    app_logger.info(f"Cleared {deleted_count} log files")
    return {"success": True, "deleted_count": deleted_count}