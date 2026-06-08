import asyncio
import json
import locale
import os
import subprocess
import uuid
from pathlib import Path
from typing import Callable, Optional
from app.config import DOWNLOAD_DIR
from app.models.schemas import DownloadStatus, DownloadProgress
from app.config_manager import get_ytdlp_path, ensure_ytdlp_installed, get_cookies_path_for_url, get_ffmpeg_path, ensure_ffmpeg_installed, get_deno_path, ensure_deno_installed
from app.models.database import DownloadTaskModel, DownloadedFileModel, get_db
from app.logger import app_logger
from datetime import datetime


def decode_ytdlp_output(data: bytes) -> str:
    """Decode yt-dlp subprocess output handling both UTF-8 and system encoding."""
    # 尝试 UTF-8 优先（大多数情况）
    try:
        return data.decode('utf-8').strip()
    except UnicodeDecodeError:
        pass
    # 尝试系统编码（如 Windows GBK）
    try:
        system_encoding = locale.getpreferredencoding()
        return data.decode(system_encoding).strip()
    except Exception:
        pass
    # 最终 fallback
    return data.decode('utf-8', errors='replace').strip()


def get_file_group_key(filename: str) -> str:
    """从文件名提取分组 key（去除扩展名和视频 ID 后缀）"""
    lower = filename.lower()
    base = lower
    # 处理 .info.json 
    if base.endswith('.info.json'):
        base = base[:-10]
    else:
        dot_idx = base.rfind('.')
        if dot_idx > 0:
            base = base[:dot_idx]
    # 去除视频 ID 后缀 [xxx]
    import re
    base = re.sub(r'\s*\[[\w-]+\]$', '', base)
    return base


def get_file_type(filename: str) -> str:
    """根据扩展名判断文件类型"""
    lower = filename.lower()
    if lower.endswith('.info.json') or lower.endswith('.json'):
        return 'info'
    if lower.endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv')):
        return 'video'
    if lower.endswith(('.webp', '.jpg', '.jpeg', '.png')):
        return 'thumbnail'
    if lower.endswith(('.mp3', '.aac', '.flac', '.wav', '.ogg', '.m4a')):
        return 'audio'
    return 'other'


def save_downloaded_file_to_db(filename: str, filepath: str, filesize: int) -> None:
    """下载完成后记录文件信息到数据库"""
    db = next(get_db())
    try:
        existing = db.query(DownloadedFileModel).filter(
            DownloadedFileModel.path == filepath
        ).first()
        if existing:
            existing.size = filesize
        else:
            record = DownloadedFileModel(
                name=filename,
                path=filepath,
                size=filesize,
                file_type=get_file_type(filename),
                group_key=get_file_group_key(filename),
            )
            db.add(record)
        db.commit()
    except Exception as e:
        app_logger.warning(f"Failed to save file record to DB: {e}")
    finally:
        db.close()


def remove_downloaded_file_from_db(filename: str) -> None:
    """删除文件时同时删除数据库记录"""
    db = next(get_db())
    try:
        db.query(DownloadedFileModel).filter(
            DownloadedFileModel.name == filename
        ).delete()
        db.commit()
    except Exception as e:
        app_logger.warning(f"Failed to remove file record from DB: {e}")
    finally:
        db.close()


def generate_nfo_from_info_json(info_json_path: str, nfo_path: str) -> Optional[str]:
    """从 yt-dlp 的 info.json 生成 NFO 文件（Emby/Jellyfin/Kodi 格式）"""
    try:
        with open(info_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        app_logger.warning(f"Failed to read info.json for NFO generation: {e}")
        return None

    def xml_escape(s):
        if not s:
            return ''
        return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

    title = data.get('title') or data.get('fulltitle') or ''
    description = data.get('description') or ''
    upload_date = data.get('upload_date', '')  # YYYYMMDD
    year = upload_date[:4] if len(upload_date) >= 4 else ''
    # aired: YYYY-MM-DD
    aired = ''
    if len(upload_date) == 8:
        aired = f'{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}'
    duration = data.get('duration')  # seconds
    runtime = str(int(duration)) if duration else ''
    uploader = data.get('uploader') or data.get('channel') or ''
    webpage_url = data.get('webpage_url', '')
    thumbnail = data.get('thumbnail', '')
    categories = data.get('categories') or []
    tags = data.get('tags') or []
    chapters = data.get('chapters') or []

    lines = []
    lines.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')
    lines.append('<movie>')
    lines.append(f'  <title>{xml_escape(title)}</title>')
    if uploader:
        lines.append(f'  <originaltitle>{xml_escape(uploader)} - {xml_escape(title)}</originaltitle>')
    if year:
        lines.append(f'  <year>{xml_escape(year)}</year>')
    if aired:
        lines.append(f'  <aired>{xml_escape(aired)}</aired>')
        lines.append(f'  <dateadded>{xml_escape(aired)}</dateadded>')
    if description:
        lines.append(f'  <plot>{xml_escape(description)}</plot>')
        lines.append(f'  <outline>{xml_escape(description)}</outline>')
    if runtime:
        lines.append(f'  <runtime>{xml_escape(runtime)}</runtime>')
    if uploader:
        lines.append(f'  <director>{xml_escape(uploader)}</director>')
        lines.append(f'  <credits>{xml_escape(uploader)}</credits>')
        lines.append(f'  <studio>{xml_escape(uploader)}</studio>')
    for cat in categories:
        lines.append(f'  <genre>{xml_escape(cat)}</genre>')
    for tag in tags:
        lines.append(f'  <tag>{xml_escape(tag)}</tag>')
    if thumbnail:
        lines.append(f'  <thumb>{xml_escape(thumbnail)}</thumb>')
    lines.append(f'  <source>{xml_escape(webpage_url)}</source>')
    lines.append(f'  <id>{xml_escape(data.get("id", ""))}</id>')

    # 章节信息 (chapters)
    for ch in chapters:
        ch_title = ch.get('title', '')
        ch_start = ch.get('start_time', 0)
        ch_end = ch.get('end_time', 0)
        if ch_title or ch_end > 0:
            lines.append('  <chapter>')
            if ch_title:
                lines.append(f'    <name>{xml_escape(ch_title)}</name>')
            lines.append(f'    <starttime>{int(ch_start)}</starttime>')
            lines.append(f'    <endtime>{int(ch_end)}</endtime>')
            lines.append('  </chapter>')

    # 视频/音频流信息 (streamdetails)
    lines.append('  <fileinfo>')
    lines.append('    <streamdetails>')
    
    # 视频流信息
    vcodec = data.get('vcodec') or ''
    acodec = data.get('acodec') or ''
    width = data.get('width') or 0
    height = data.get('height') or 0
    fps = data.get('fps') or ''
    
    if vcodec and vcodec != 'none':
        lines.append('      <video>')
        lines.append(f'        <codec>{xml_escape(vcodec)}</codec>')
        if width and height:
            lines.append(f'        <width>{int(width)}</width>')
            lines.append(f'        <height>{int(height)}</height>')
            lines.append(f'        <aspect>{float(width)/float(height):.4f}</aspect>')
        if fps:
            lines.append(f'        <framerate>{xml_escape(str(fps))}</framerate>')
        if duration:
            lines.append(f'        <duration>{int(duration)}</duration>')
        lines.append('        <bitrate/>')
        lines.append('      </video>')
    
    # 音频流信息
    if acodec and acodec != 'none':
        lines.append('      <audio>')
        lines.append(f'        <codec>{xml_escape(acodec)}</codec>')
        if duration:
            lines.append(f'        <duration>{int(duration)}</duration>')
        lines.append(f'        <bitrate/>')
        lines.append('      </audio>')
    
    lines.append('    </streamdetails>')
    lines.append('  </fileinfo>')

    lines.append('</movie>')

    nfo_content = '\n'.join(lines) + '\n'

    try:
        with open(nfo_path, 'w', encoding='utf-8') as f:
            f.write(nfo_content)
        app_logger.info(f"NFO file generated: {nfo_path}")
        return nfo_path
    except Exception as e:
        app_logger.warning(f"Failed to write NFO file: {e}")
        return None


def convert_thumbnail_to_jpg(filepath: str) -> Optional[str]:
    """Convert thumbnail image to JPG format. Supports webp, png, etc."""
    try:
        from PIL import Image
        path = Path(filepath)
        if not path.exists():
            return None
        
        # 只处理非 jpg 的图片
        ext = path.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            return str(path)
        
        jpg_path = path.with_suffix('.jpg')
        with Image.open(str(path)) as img:
            # Convert RGBA/P to RGB for JPG
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            img.save(str(jpg_path), 'JPEG', quality=85)
        
        # 删除原始文件（只删除 webp，保留其他格式）
        if ext == '.webp':
            path.unlink()
        
        app_logger.info(f"Thumbnail converted: {path.name} -> {jpg_path.name}")
        return str(jpg_path)
    except Exception as e:
        app_logger.warning(f"Failed to convert thumbnail {filepath}: {e}")
        return None


def get_ytdlp_env():
    """Get environment variables for yt-dlp subprocess, matching sample-project configuration."""
    # 复制当前环境变量，确保系统 PATH 等被保留
    env = os.environ.copy()
    # 设置 Deno 相关环境变量
    env['DENO_NO_PROMPT'] = '1'
    env['DENO_DIR'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'deno')
    env['XDG_CACHE_HOME'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'cache')
    # 添加 ffmpeg 到 PATH
    ffmpeg_dir = os.path.dirname(get_ffmpeg_path())
    if os.path.exists(ffmpeg_dir):
        env['PATH'] = ffmpeg_dir + os.pathsep + env.get('PATH', '')
    # 添加 deno 到 PATH
    deno_dir = os.path.dirname(get_deno_path())
    if os.path.exists(deno_dir):
        env['PATH'] = deno_dir + os.pathsep + env.get('PATH', '')
    return env


class DownloadTask:
    def __init__(self, task_id: str, url: str, options: dict, title: Optional[str] = None):
        self.task_id = task_id
        self.url = url
        self.options = options
        self.title = title  # 视频标题
        self.status = DownloadStatus.PENDING
        self.filename: Optional[str] = None
        self.progress: float = 0.0
        self.stage: Optional[str] = None  # 当前阶段
        self.speed: Optional[str] = None
        self.eta: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at: Optional[float] = None  # Unix timestamp
        self._process = None
        self._stdout_reader = None

    def to_progress(self) -> DownloadProgress:
        return DownloadProgress(
            task_id=self.task_id,
            status=self.status,
            url=self.url,
            filename=self.filename,
            title=self.title,
            progress=self.progress,
            stage=self.stage,
            speed=self.speed,
            eta=self.eta,
            error=self.error,
            created_at=self.created_at
        )

    def __repr__(self):
        return f"<DownloadTask id={self.task_id} url={self.url} status={self.status} options={self.options}>"


class DownloadManager:
    def __init__(self):
        self.tasks: dict[str, DownloadTask] = {}
        self.progress_callbacks: list[Callable] = []
        self._load_tasks_from_db()
        app_logger.info(f"DownloadManager initialized with {len(self.tasks)} tasks from DB")

    def _load_tasks_from_db(self):
        """从数据库加载所有任务"""
        app_logger.debug("Loading tasks from database...")
        try:
            db = next(get_db())
            # 加载所有状态的任务，包括已完成/失败的，这样重启后用户仍可看到历史
            db_tasks = db.query(DownloadTaskModel).all()
            
            app_logger.debug(f"Found {len(db_tasks)} tasks in database")
            
            for db_task in db_tasks:
                task = DownloadTask(
                    task_id=db_task.id,
                    url=db_task.url,
                    options={
                        'format': db_task.format,
                        'output_template': db_task.output_template,
                        'audio_only': db_task.audio_only
                    },
                    title=db_task.title
                )
                task.status = DownloadStatus(db_task.status)
                task.filename = db_task.filename
                task.title = db_task.title
                task.progress = db_task.progress
                task.stage = db_task.stage
                task.speed = db_task.speed
                task.eta = db_task.eta
                task.error = db_task.error
                if db_task.created_at:
                    task.created_at = db_task.created_at.timestamp()
                self.tasks[db_task.id] = task
                app_logger.debug(f"Loaded task from DB: {task}")
        except Exception as e:
            app_logger.error(f"Failed to load tasks from database: {e}")

    def _save_task_to_db(self, task: DownloadTask):
        """保存任务到数据库"""
        db = next(get_db())
        try:
            db_task = db.query(DownloadTaskModel).filter(DownloadTaskModel.id == task.task_id).first()
            
            if not db_task:
                db_task = DownloadTaskModel(id=task.task_id)
                app_logger.debug(f"Creating new DB record for task {task.task_id}")
            
            db_task.url = task.url
            db_task.status = task.status.value
            db_task.filename = task.filename
            db_task.title = task.title
            db_task.progress = task.progress
            db_task.stage = task.stage
            db_task.speed = task.speed
            db_task.eta = task.eta
            db_task.error = task.error
            db_task.format = task.options.get('format', 'best')
            db_task.audio_only = task.options.get('audio_only', False)
            db_task.output_template = task.options.get('output_template', '%(title)s.%(ext)s')
            
            if task.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
                db_task.completed_at = datetime.utcnow()
            
            db.add(db_task)
            db.commit()
            app_logger.debug(f"Task {task.task_id} saved to DB: status={task.status.value}, progress={task.progress}%")
        except Exception as e:
            app_logger.error(f"Failed to save task to database: {e}")
        finally:
            db.close()

    def add_progress_callback(self, callback: Callable):
        self.progress_callbacks.append(callback)
        app_logger.debug(f"Added progress callback: {callback}")

    async def notify_progress(self, task: DownloadTask):
        """通知所有回调任务进度变化"""
        progress = task.to_progress()
        app_logger.debug(f"Notifying progress for task {task.task_id}: {task.status.value} - {task.progress}%")
        for callback in self.progress_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(progress)
            else:
                callback(progress)

    def create_task(self, url: str, format: str = "best", audio_only: bool = False,
                    output_template: str = "%(title)s.%(ext)s", video_format_id: Optional[str] = None,
                    title: Optional[str] = None) -> str:
        task_id = str(uuid.uuid4())[:8]

        options = {
            'format': 'bestaudio[ext=m4a]' if audio_only else format,
            'output_template': output_template,
            'audio_only': audio_only,
            'video_format_id': video_format_id,
        }

        task = DownloadTask(task_id, url, options, title=title)
        task.created_at = datetime.utcnow().timestamp()
        self.tasks[task_id] = task
        self._save_task_to_db(task)
        
        app_logger.info(
            f"Task created: id={task_id}, url={url}, title={title}, audio_only={audio_only}, "
            f"format={options['format']}, video_format_id={video_format_id}"
        )
        return task_id

    async def _parse_progress_line(self, line: str, task: DownloadTask):
        """Parse yt-dlp progress output line"""
        try:
            if '%' in line and 'ETA' in line:
                parts = line.split()
                for part in parts:
                    if '%' in part:
                        try:
                            old_progress = task.progress
                            task.progress = float(part.replace('%', '').strip())
                            if int(task.progress) != int(old_progress):
                                app_logger.debug(f"Task {task.task_id} progress: {task.progress}%")
                        except ValueError:
                            pass
                    elif part.startswith('ETA'):
                        task.eta = part.replace('ETA', '').strip()
                    elif part.endswith('B/s') or part.endswith('KiB/s') or part.endswith('MiB/s'):
                        task.speed = part
            elif 'Destination' in line:
                filename = line.split(':')[-1].strip()
                task.filename = Path(filename).name
                app_logger.info(f"Task {task.task_id} destination file: {task.filename}")
            elif 'Merging' in line and 'into' in line:
                # [Merger] Merging formats into "Video Title [abc123].mkv"
                # 提取最终合并后的文件名（覆盖之前的临时文件名）
                import re
                m = re.search(r'into\s+"([^"]+)"', line)
                if m:
                    task.filename = Path(m.group(1)).name
                    app_logger.info(f"Task {task.task_id} merged file: {task.filename}")
            elif 'has already been downloaded' in line:
                task.progress = 100.0
                task.status = DownloadStatus.COMPLETED
                app_logger.info(f"Task {task.task_id} file already exists")
            elif 'error' in line.lower() or 'warning' in line.lower():
                app_logger.warning(f"Task {task.task_id} yt-dlp output: {line}")
        except Exception:
            pass

    async def start_download(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            app_logger.error(f"Task {task_id} not found in task list")
            return

        app_logger.info(f"="*60)
        app_logger.info(f"Starting download: task_id={task_id}")
        app_logger.info(f"URL: {task.url}")
        app_logger.info(f"Options: {task.options}")
        app_logger.info(f"="*60)
        
        # 检查 yt-dlp 是否安装
        if not ensure_ytdlp_installed():
            task.status = DownloadStatus.FAILED
            task.error = "Failed to download yt-dlp executable"
            app_logger.error(f"Task {task_id}: yt-dlp not installed or download failed")
            self._save_task_to_db(task)
            await self.notify_progress(task)
            return
        
        # 检查 ffmpeg 是否安装（用于合并视频+音频）
        if not ensure_ffmpeg_installed():
            app_logger.warning(f"Task {task_id}: ffmpeg not available, video merging will be skipped")
        
        # 检查 deno 是否安装（用于 YouTube 验证）
        if not ensure_deno_installed():
            app_logger.warning(f"Task {task_id}: deno not available, JS challenge solving may fail")

        task.status = DownloadStatus.DOWNLOADING
        task.stage = 'extracting'
        app_logger.info(f"Task {task_id}: Status changed to DOWNLOADING")
        self._save_task_to_db(task)
        await self.notify_progress(task)

        try:
            ytdlp_path = get_ytdlp_path()
            app_logger.info(f"Task {task_id}: yt-dlp path: {ytdlp_path}")
            
            # 检查 yt-dlp 文件是否存在
            import os
            if not os.path.exists(ytdlp_path):
                app_logger.error(f"Task {task_id}: yt-dlp executable not found at {ytdlp_path}")
                task.status = DownloadStatus.FAILED
                task.error = f"yt-dlp executable not found at {ytdlp_path}"
                self._save_task_to_db(task)
                await self.notify_progress(task)
                return
            
            # Build command arguments - URL should be at the end for yt-dlp
            args = [ytdlp_path]
            
            # Add JS runtime for yt-dlp (important for YouTube validation)
            args.extend(['--js-runtime', 'deno'])
            
            # Output template
            output_path = str(DOWNLOAD_DIR / task.options['output_template'])
            args.extend(['-o', output_path])
            app_logger.info(f"Task {task_id}: Output template: {output_path}")
            
            # Format options
            if task.options.get('audio_only'):
                args.extend(['-f', 'bestaudio[ext=m4a]', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '192'])
                app_logger.info(f"Task {task_id}: Audio only mode - using bestaudio[ext=m4a], extracting to MP3")
            else:
                # Check if user selected a specific format
                video_format_id = task.options.get('video_format_id')
                if video_format_id:
                    # Use the selected format with best audio
                    args.extend(['-f', f'{video_format_id}+bestaudio[ext=m4a]'])
                    app_logger.info(f"Task {task_id}: Using selected video format: {video_format_id}")
                    app_logger.info(f"Task {task_id}: Format selector: {video_format_id}+bestaudio[ext=m4a]")
                else:
                    # Use bestvideo+bestaudio with merge to mkv/mp4 format
                    args.extend(['-f', 'bestvideo+bestaudio[ext=m4a]/best'])
                    app_logger.info(f"Task {task_id}: No specific format selected, using bestvideo+bestaudio[ext=m4a]/best")
                
                container_format = task.options.get('format', 'mp4')
                args.extend(['--merge-output-format', container_format])
                app_logger.info(f"Task {task_id}: Container format: {container_format}")
            
            # Cookies
            cookies_path = get_cookies_path_for_url(task.url)
            if cookies_path:
                args.extend(['--cookies', cookies_path])
                app_logger.info(f"Task {task_id}: Using cookies from: {cookies_path}")
            else:
                app_logger.info(f"Task {task_id}: No cookies file for this URL")
            
            # Progress options
            args.append('--newline')
            
            # Write info json for better debugging
            args.extend(['--write-info-json'])
            
            # Download thumbnail
            args.extend(['--write-thumbnail'])
            
            # URL at the end
            args.append(task.url)

            # 输出完整命令（便于复制执行调试）
            full_command = ' '.join(args)
            app_logger.info("="*60)
            app_logger.info(f"Task {task_id}: YT-DLP FULL COMMAND (copy to debug)")
            app_logger.info("="*60)
            app_logger.info(f"> {full_command}")
            app_logger.info("="*60)
            app_logger.info(f"Task {task_id}: Working directory: {DOWNLOAD_DIR}")
            
            # 执行下载（使用 sample-project 相同的环境变量配置）
            env = get_ytdlp_env()
            app_logger.info(f"Task {task_id}: Starting subprocess...")
            app_logger.info(f"Task {task_id}: Environment: DENO_NO_PROMPT=1, DENO_DIR={env.get('DENO_DIR')}, XDG_CACHE_HOME={env.get('XDG_CACHE_HOME')}")
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(DOWNLOAD_DIR),
                env=env
            )
            task._process = process
            app_logger.info(f"Task {task_id}: Process started with PID {process.pid}")
            
            # 更新阶段为 downloading
            task.stage = 'downloading'
            self._save_task_to_db(task)
            await self.notify_progress(task)
            
            # Collect all output for debugging
            output_lines = []
            line_count = 0

            app_logger.info(f"Task {task_id}: Reading output...")
            while True:
                line = await process.stdout.readline()
                if not line:
                    app_logger.debug(f"Task {task_id}: EOF reached, total lines: {line_count}")
                    break
                
                line_count += 1
                line_str = decode_ytdlp_output(line)
                output_lines.append(line_str)
                
                # Log first 50 lines and every 100th line at info level
                if line_count <= 50 or line_count % 100 == 0:
                    app_logger.info(f"Task {task_id} [{line_count}]: {line_str[:200]}")
                
                await self._parse_progress_line(line_str, task)
                self._save_task_to_db(task)
                await self.notify_progress(task)

            app_logger.info(f"Task {task_id}: Process finished, waiting for completion...")
            await process.wait()
            app_logger.info(f"Task {task_id}: Process exited with return code: {process.returncode}")

            if process.returncode == 0:
                task.status = DownloadStatus.COMPLETED
                task.progress = 100.0
                task.stage = 'finalizing'
                app_logger.info(f"="*60)
                app_logger.info(f"Task {task_id}: SUCCESS - Download completed!")
                
                # 记录所有下载文件到数据库
                if task.filename:
                    video_path = DOWNLOAD_DIR / task.filename
                    group_key = get_file_group_key(task.filename)
                    app_logger.info(f"Task {task_id}: Recording files, group_key={group_key}")
                    
                    # 记录主视频文件
                    if video_path.exists():
                        save_downloaded_file_to_db(
                            task.filename, str(video_path), video_path.stat().st_size
                        )
                    else:
                        app_logger.warning(f"Task {task_id}: Main video file not found: {task.filename}")
                    
                    # 记录同组的其他文件（缩略图、info.json 等）
                    for f in DOWNLOAD_DIR.iterdir():
                        if f.is_file() and f.name != task.filename:
                            f_group = get_file_group_key(f.name)
                            if f_group == group_key:
                                save_downloaded_file_to_db(f.name, str(f), f.stat().st_size)
                                # 转换缩略图
                                if get_file_type(f.name) == 'thumbnail':
                                    convert_thumbnail_to_jpg(str(f))
                                # 从 info.json 生成 NFO 文件
                                if get_file_type(f.name) == 'info':
                                    # info.json -> .nfo (去掉 .info 中间部分)
                                    info_str = str(f)
                                    if info_str.endswith('.info.json'):
                                        nfo_path = info_str[:-10] + '.nfo'
                                    else:
                                        nfo_path = str(f.with_suffix('.nfo'))
                                    if not Path(nfo_path).exists():
                                        generated = generate_nfo_from_info_json(str(f), nfo_path)
                                        if generated and Path(nfo_path).exists():
                                            save_downloaded_file_to_db(Path(nfo_path).name, nfo_path, Path(nfo_path).stat().st_size)
                else:
                    app_logger.warning(f"Task {task_id}: task.filename is None, file recording skipped")
                
                task.stage = None
                app_logger.info(f"Task {task_id}: Filename: {task.filename}")
                app_logger.info(f"="*60)
            else:
                task.status = DownloadStatus.FAILED
                # Show last 20 lines of output as error message
                error_output = '\n'.join(output_lines[-20:])
                task.error = f"Download failed with code {process.returncode}\nOutput:\n{error_output}"
                app_logger.error(f"="*60)
                app_logger.error(f"Task {task_id}: FAILED - Download failed with code {process.returncode}")
                app_logger.error(f"Task {task_id}: Last 20 lines of output:")
                for line in output_lines[-20:]:
                    app_logger.error(f"  {line}")
                app_logger.error(f"="*60)

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error = str(e)
            app_logger.exception(f"Task {task_id}: Exception occurred during download")
            app_logger.error(f"Task {task_id}: Exception details: {e}")

        self._save_task_to_db(task)
        await self.notify_progress(task)
        app_logger.info(f"Task {task_id}: Final status: {task.status.value}, progress: {task.progress}%")

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        task = self.tasks.get(task_id)
        app_logger.debug(f"get_task({task_id}): {task}")
        return task

    def get_all_tasks(self) -> list[DownloadTask]:
        tasks = list(self.tasks.values())
        app_logger.debug(f"get_all_tasks: returning {len(tasks)} tasks")
        return tasks

    def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task.status == DownloadStatus.DOWNLOADING:
            if task._process:
                app_logger.info(f"cancel_task({task_id}): Terminating process")
                task._process.terminate()
            task.status = DownloadStatus.CANCELLED
            self._save_task_to_db(task)
            app_logger.info(f"cancel_task({task_id}): Task cancelled")
            return True
        app_logger.warn(f"cancel_task({task_id}): Task not found or not in downloading state")
        return False

    def remove_task(self, task_id: str) -> bool:
        """从内存、数据库和磁盘中删除任务记录及关联文件"""
        app_logger.info(f"remove_task({task_id}): Starting...")
        try:
            # 获取任务信息（优先从内存，其次从数据库）
            task = self.tasks.get(task_id)
            task_filename = None
            if task:
                task_filename = task.filename
                app_logger.debug(f"remove_task({task_id}): Got filename from memory: {task_filename}")
            
            # 从内存中移除
            if task_id in self.tasks:
                del self.tasks[task_id]
                app_logger.debug(f"remove_task({task_id}): Removed from memory")
            
            # 从数据库中删除
            db = next(get_db())
            try:
                db_task = db.query(DownloadTaskModel).filter(DownloadTaskModel.id == task_id).first()
                if db_task:
                    # 如果还没获取到文件名，从 DB 获取
                    if not task_filename:
                        task_filename = db_task.filename
                    db.delete(db_task)
                    db.commit()
                    app_logger.info(f"remove_task({task_id}): Removed from database")
                
                # 删除关联的物理文件和数据库记录
                if task_filename:
                    self._delete_associated_files(task_filename)
                else:
                    app_logger.warning(f"remove_task({task_id}): No filename available, skipping file deletion")
                
                return True
            finally:
                db.close()
        except Exception as e:
            app_logger.error(f"remove_task({task_id}): Failed - {e}")
            return False

    def _delete_associated_files(self, filename: str):
        """删除与指定文件同组的所有物理文件，并从 DB 删除记录"""
        group_key = get_file_group_key(filename)
        app_logger.info(f"Deleting files for group: {group_key}")
        deleted_count = 0
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file():
                f_group = get_file_group_key(f.name)
                if f_group == group_key:
                    try:
                        f.unlink()
                        deleted_count += 1
                        app_logger.debug(f"Deleted file: {f.name}")
                    except Exception as e:
                        app_logger.warning(f"Failed to delete file {f.name}: {e}")
                    # 同时删除 DB 记录
                    remove_downloaded_file_from_db(f.name)
        app_logger.info(f"Deleted {deleted_count} files for group: {group_key}")

    def get_history(self) -> list[DownloadTask]:
        """获取历史任务记录"""
        app_logger.debug("get_history: Loading completed/failed tasks from database")
        history = []
        db = next(get_db())
        try:
            db_tasks = db.query(DownloadTaskModel).filter(
                DownloadTaskModel.status.in_([DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value, DownloadStatus.CANCELLED.value])
            ).order_by(DownloadTaskModel.completed_at.desc()).all()
            
            app_logger.debug(f"get_history: Found {len(db_tasks)} history records")
            
            for db_task in db_tasks:
                task = DownloadTask(
                    task_id=db_task.id,
                    url=db_task.url,
                    options={
                        'format': db_task.format,
                        'output_template': db_task.output_template,
                        'audio_only': db_task.audio_only
                    }
                )
                task.status = DownloadStatus(db_task.status)
                task.filename = db_task.filename
                task.progress = db_task.progress
                task.speed = db_task.speed
                task.eta = db_task.eta
                task.error = db_task.error
                if db_task.created_at:
                    task.created_at = db_task.created_at.timestamp()
                history.append(task)
        except Exception as e:
            app_logger.error(f"get_history: Failed - {e}")
        finally:
            db.close()
        
        return history


download_manager = DownloadManager()
