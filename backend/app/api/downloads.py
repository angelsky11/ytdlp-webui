import asyncio
import json
import os
import subprocess
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import DownloadRequest, DownloadProgress, VideoInfo, VideoFormat
from app.services.downloader import download_manager, get_ytdlp_env
from app.config_manager import get_ytdlp_path, get_cookies_path_for_url, ensure_deno_installed
from app.logger import app_logger

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.post("/", response_model=DownloadProgress)
async def create_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    app_logger.info("="*60)
    app_logger.info("API: POST /downloads/")
    app_logger.info(f"Request: {request}")
    app_logger.info("="*60)
    
    task_id = download_manager.create_task(
        url=request.url,
        format=request.format,
        audio_only=request.audio_only,
        output_template=request.output_template,
        video_format_id=request.video_format_id,
        title=request.title
    )
    
    app_logger.info(f"Task created with id: {task_id}")
    
    # Add download task to background
    background_tasks.add_task(download_manager.start_download, task_id)
    app_logger.info(f"Download task scheduled for background execution")
    
    task = download_manager.get_task(task_id)
    progress = task.to_progress() if task else None
    app_logger.info(f"Returning progress: {progress}")
    
    return progress


@router.get("/{task_id}", response_model=DownloadProgress)
async def get_download_status(task_id: str):
    app_logger.debug(f"API: GET /downloads/{task_id}")
    task = download_manager.get_task(task_id)
    if not task:
        app_logger.warn(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_progress()


@router.get("/", response_model=list[DownloadProgress])
async def list_downloads():
    app_logger.debug("API: GET /downloads/")
    tasks = download_manager.get_all_tasks()
    app_logger.debug(f"Returning {len(tasks)} tasks")
    return [task.to_progress() for task in tasks]


@router.delete("/{task_id}")
async def cancel_download(task_id: str):
    app_logger.info(f"API: DELETE /downloads/{task_id}")
    if not download_manager.cancel_task(task_id):
        app_logger.warn(f"Failed to cancel task {task_id}")
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    app_logger.info(f"Task {task_id} cancelled successfully")
    return {"message": "Download cancelled"}


@router.delete("/{task_id}/remove")
async def remove_download(task_id: str):
    """删除任务记录（从数据库中移除）"""
    app_logger.info(f"API: DELETE /downloads/{task_id}/remove")
    result = download_manager.remove_task(task_id)
    if not result:
        app_logger.warn(f"Failed to remove task {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    app_logger.info(f"Task {task_id} removed successfully")
    return {"message": "Task removed"}


@router.get("/history", response_model=list[DownloadProgress])
async def list_download_history():
    """获取下载历史记录"""
    app_logger.debug("API: GET /downloads/history")
    history = download_manager.get_history()
    app_logger.debug(f"Returning {len(history)} history records")
    return [task.to_progress() for task in history]


@router.post("/info", response_model=VideoInfo)
async def get_video_info(request: DownloadRequest):
    """获取视频信息（使用 subprocess 直接执行 yt-dlp 命令行，匹配 sample-project 方式）"""
    app_logger.info("="*60)
    app_logger.info("API: POST /downloads/info")
    app_logger.info(f"URL: {request.url}")
    app_logger.info("="*60)
    
    try:
        ytdlp_path = get_ytdlp_path()
        cookies_path = get_cookies_path_for_url(request.url)
        
        # 确保 deno 已安装（用于 YouTube JS 挑战）
        app_logger.info("Ensuring Deno is installed...")
        ensure_deno_installed()
        
        # 构建命令参数（使用 deno 运行时，去除多余参数）
        args = [
            ytdlp_path,
            '--dump-json',
            '--no-playlist',
            '--no-warnings',
            # deno 运行时（yt-dlp 推荐，处理 YouTube JS 挑战）
            '--js-runtime', 'deno',
            # cookies
            '--cookies', cookies_path if cookies_path else '',
        ]
        
        # 移除空的 cookies 参数
        args = [arg for arg in args if arg != '']
        
        # 添加 URL
        args.append(request.url)
        
        # 获取环境变量
        env = get_ytdlp_env()
        app_logger.info(f"Using yt-dlp: {ytdlp_path}")
        app_logger.info(f"Using cookies: {cookies_path}")
        app_logger.info(f"Environment: DENO_NO_PROMPT=1, DENO_DIR={env.get('DENO_DIR')}, XDG_CACHE_HOME={env.get('XDG_CACHE_HOME')}")
        
        # 输出完整命令
        full_command = ' '.join(args)
        app_logger.info("="*60)
        app_logger.info("YT-DLP INFO COMMAND (copy to debug)")
        app_logger.info("="*60)
        app_logger.info(f"> {full_command}")
        app_logger.info("="*60)
        
        # 执行命令
        app_logger.info("Extracting video info...")
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode('utf-8', errors='replace').strip()
        stderr_str = stderr.decode('utf-8', errors='replace').strip()
        
        if process.returncode != 0:
            app_logger.error(f"yt-dlp failed with code {process.returncode}")
            app_logger.error(f"stderr: {stderr_str[:500]}")
            raise HTTPException(status_code=400, detail=f"Failed to get video info: {stderr_str[:200]}")
        
        # 解析 JSON 输出
        if not stdout_str:
            app_logger.error("No output from yt-dlp")
            raise HTTPException(status_code=400, detail="No video info returned")
        
        try:
            # 尝试解析多行 JSON（yt-dlp 可能输出多行）
            lines = stdout_str.strip().split('\n')
            info = None
            for line in lines:
                if line.strip():
                    info = json.loads(line)
                    break
            
            if not info:
                # 尝试直接解析
                info = json.loads(stdout_str)
        except json.JSONDecodeError as e:
            app_logger.error(f"Failed to parse JSON: {e}")
            app_logger.error(f"Output: {stdout_str[:500]}")
            raise HTTPException(status_code=400, detail=f"Failed to parse video info: {str(e)}")
        
        app_logger.info(f"Video title: {info.get('title', 'N/A')}")
        app_logger.info(f"Total formats found: {len(info.get('formats', []))}")
        
        # Parse formats to VideoFormat objects, filtering video+audio combined formats
        formats = []
        for f in info.get('formats', []):
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')
            filesize = f.get('filesize')
            
            # 过滤条件：有视频轨道 AND filesize 不为空
            if vcodec and vcodec != 'none' and filesize:
                formats.append(VideoFormat(
                    format_id=f.get('format_id', ''),
                    ext=f.get('ext', ''),
                    resolution=f.get('resolution'),
                    fps=f.get('fps'),
                    filesize=filesize,
                    vcodec=vcodec,
                    acodec=acodec if acodec else None,
                    format_note=f.get('format_note')
                ))
        
        app_logger.info(f"Filtered formats (with video): {len(formats)}")
        
        # Sort by resolution (height) descending
        formats.sort(key=lambda x: int(x.resolution.split('x')[1]) if x.resolution and 'x' in x.resolution else 0, reverse=True)
        
        # Limit to top 20 formats
        formats = formats[:20]
        app_logger.info(f"Returning top {len(formats)} formats")
        
        # Log format details
        for fmt in formats[:5]:
            app_logger.info(f"  Format: {fmt.format_id} - {fmt.resolution} - {fmt.ext} - {fmt.fps}fps")
        
        result = VideoInfo(
            title=info.get('title', ''),
            thumbnail=info.get('thumbnail'),
            duration=info.get('duration'),
            uploader=info.get('uploader'),
            formats=formats
        )
        
        app_logger.info("Video info extracted successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(f"Failed to get video info: {e}")
        raise HTTPException(status_code=400, detail=str(e))
