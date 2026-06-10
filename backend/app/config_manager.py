import os
import json
import subprocess
import platform
from typing import Optional, List
from pydantic import BaseModel
from app.config import CONFIG_DIR, DOWNLOAD_DIR
from app.utils.download import download_executable, download_and_extract_zip, download_and_extract_tarxz

class AppConfig(BaseModel):
    default_format: str = "mp4"
    ytdlp_version: str = "stable"
    cookies_enabled: bool = True
    log_level: str = "info"
    language: str = "en"

def get_logs_dir():
    """Get logs directory"""
    logs_dir = os.path.join(str(CONFIG_DIR), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

LOGS_DIR = get_logs_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def get_ytdlp_dir():
    return os.path.join(CONFIG_DIR, "ytdlp")

def get_ytdlp_path():
    """Get path to yt-dlp executable"""
    os.makedirs(get_ytdlp_dir(), exist_ok=True)
    
    system = platform.system()
    if system == "Windows":
        return os.path.join(get_ytdlp_dir(), "yt-dlp.exe")
    else:
        return os.path.join(get_ytdlp_dir(), "yt-dlp")

def get_cookies_dir():
    """Get cookies directory"""
    cookies_dir = os.path.join(CONFIG_DIR, "cookies")
    os.makedirs(cookies_dir, exist_ok=True)
    return cookies_dir

def load_config() -> AppConfig:
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception:
            pass
    return AppConfig()

def save_config(config: AppConfig) -> None:
    """Save configuration to file"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config.model_dump(), f, indent=2)

def get_default_format() -> str:
    """Get default video format"""
    config = load_config()
    return config.default_format

def set_default_format(format: str) -> None:
    """Set default video format"""
    if format not in ["mp4", "mkv"]:
        raise ValueError("Format must be mp4 or mkv")
    config = load_config()
    config.default_format = format
    save_config(config)

def get_ytdlp_version() -> str:
    """Get yt-dlp version setting (stable or nightly)"""
    config = load_config()
    return config.ytdlp_version

def set_ytdlp_version(version: str) -> None:
    """Set yt-dlp version setting"""
    if version not in ["stable", "nightly"]:
        raise ValueError("Version must be 'stable' or 'nightly'")
    config = load_config()
    config.ytdlp_version = version
    save_config(config)

def get_ytdlp_current_version() -> str:
    """Get current yt-dlp installed version"""
    ytdlp_path = get_ytdlp_path()
    if not os.path.exists(ytdlp_path):
        return "Not installed"
    
    try:
        result = subprocess.run(
            [ytdlp_path, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return "Unknown"

def download_ytdlp() -> dict:
    """Download yt-dlp executable to the configured version"""
    version = get_ytdlp_version()
    system = platform.system()
    
    if version == "nightly":
        if system == "Windows":
            url = "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp.exe"
        else:
            url = "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp"
    else:
        if system == "Windows":
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        else:
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    
    ytdlp_path = get_ytdlp_path()
    result = download_executable(url, ytdlp_path)
    
    if result["success"]:
        new_version = get_ytdlp_current_version()
        result.update({
            "version": new_version,
            "type": version
        })
    
    return result

def ensure_ytdlp_installed() -> bool:
    """Ensure yt-dlp is installed, download if not"""
    ytdlp_path = get_ytdlp_path()
    if not os.path.exists(ytdlp_path):
        result = download_ytdlp()
        return result.get("success", False)
    return True


def get_ffmpeg_dir():
    """Get ffmpeg directory"""
    return os.path.join(CONFIG_DIR, "ffmpeg")


def get_ffmpeg_path():
    """Get path to ffmpeg executable"""
    system = platform.system()
    if system == "Windows":
        return os.path.join(get_ffmpeg_dir(), "ffmpeg.exe")
    else:
        return os.path.join(get_ffmpeg_dir(), "ffmpeg")


def ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed and working"""
    from app.logger import app_logger
    
    ffmpeg_path = get_ffmpeg_path()
    
    # First check system ffmpeg in PATH
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        if result.returncode == 0:
            return True
    except Exception:
        pass
    
    # Then check local ffmpeg installation
    if os.path.exists(ffmpeg_path):
        try:
            result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, check=True)
            if result.returncode == 0:
                return True
        except Exception:
            # ffmpeg exists but can't run (e.g., wrong architecture)
            # Remove broken installation so it can be re-downloaded
            app_logger.warning(f"ffmpeg exists but not executable, removing: {ffmpeg_path}")
            os.remove(ffmpeg_path)
    
    return False


def download_ffmpeg() -> dict:
    """Download ffmpeg to config directory"""
    from app.logger import app_logger
    
    ffmpeg_dir = get_ffmpeg_dir()
    os.makedirs(ffmpeg_dir, exist_ok=True)
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Download ffmpeg Windows build from BtbN
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            success = download_and_extract_zip(
                url, ffmpeg_dir, 
                target_filename="ffmpeg.exe",
                filter_func=lambda x: x.endswith('ffmpeg.exe')
            )
        else:
            # Linux/macOS - download static build
            url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
            success = download_and_extract_tarxz(
                url, ffmpeg_dir,
                target_filename="ffmpeg",
                filter_func=lambda x: 'ffmpeg' in x and '/' not in x.replace('ffmpeg', '')
            )
        
        if success:
            app_logger.info(f"ffmpeg installed at: {get_ffmpeg_path()}")
            return {"success": True, "path": get_ffmpeg_path()}
        else:
            return {"success": False, "error": "Download or extraction failed"}
    except Exception as e:
        app_logger.error(f"Failed to download ffmpeg: {e}")
        return {"success": False, "error": str(e)}


def ensure_ffmpeg_installed() -> bool:
    """Ensure ffmpeg is installed"""
    if ffmpeg_installed():
        return True
    result = download_ffmpeg()
    return result.get("success", False)


def get_deno_dir():
    """Get deno directory"""
    deno_dir = os.path.join(CONFIG_DIR, "deno")
    os.makedirs(deno_dir, exist_ok=True)
    return deno_dir


def get_deno_path():
    """Get path to deno executable"""
    deno_dir = get_deno_dir()
    system = platform.system()
    if system == "Windows":
        return os.path.join(deno_dir, "deno.exe")
    else:
        return os.path.join(deno_dir, "deno")


def deno_installed() -> bool:
    """Check if deno is installed"""
    deno_path = get_deno_path()
    if os.path.exists(deno_path):
        return True
    try:
        subprocess.run([deno_path, "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def download_deno() -> dict:
    """Download deno to config directory"""
    from app.logger import app_logger
    
    deno_dir = get_deno_dir()
    system = platform.system()
    
    try:
        if system == "Windows":
            url = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"
            success = download_and_extract_zip(url, deno_dir)
        elif system == "Darwin":
            url = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-apple-darwin.zip"
            success = download_and_extract_zip(url, deno_dir)
        else:
            # Linux
            url = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip"
            success = download_and_extract_zip(url, deno_dir)
        
        if success:
            app_logger.info(f"Deno installed at: {get_deno_path()}")
            return {"success": True, "path": get_deno_path()}
        else:
            return {"success": False, "error": "Download or extraction failed"}
    except Exception as e:
        app_logger.error(f"Failed to download Deno: {e}")
        return {"success": False, "error": str(e)}


def ensure_deno_installed() -> bool:
    """Ensure deno is installed"""
    if deno_installed():
        return True
    result = download_deno()
    return result.get("success", False)


def is_cookies_enabled() -> bool:
    """Check if cookies are enabled"""
    config = load_config()
    return config.cookies_enabled

def get_cookies_files() -> List[dict]:
    """List all cookies files"""
    cookies_dir = get_cookies_dir()
    files = []
    
    if os.path.exists(cookies_dir):
        for f in os.listdir(cookies_dir):
            if f.endswith('.txt'):
                file_path = os.path.join(cookies_dir, f)
                files.append({
                    "name": f,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                })
    
    return files

def save_cookies(filename: str, content: bytes) -> dict:
    """Save a cookies file"""
    try:
        cookies_dir = get_cookies_dir()
        file_path = os.path.join(cookies_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {"success": True, "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_cookies(filename: str) -> dict:
    """Delete a cookies file"""
    try:
        cookies_dir = get_cookies_dir()
        file_path = os.path.join(cookies_dir, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"success": True}
        return {"success": False, "error": "File not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_cookies_path_for_url(url: str) -> Optional[str]:
    """Get cookies file path based on URL domain"""
    if not is_cookies_enabled():
        return None
    
    cookies_files = get_cookies_files()
    if not cookies_files:
        return None
    
    # Try to match filename with domain
    # Common patterns: youtube.txt, twitch.txt, etc.
    for cf in cookies_files:
        name = cf["name"].lower().replace(".txt", "")
        if name in url.lower():
            return cf["path"]
    
    # Return first cookies file if no match
    return cookies_files[0]["path"] if cookies_files else None

def get_log_level() -> str:
    """Get log level setting"""
    config = load_config()
    return config.log_level

def set_log_level(level: str) -> None:
    """Set log level setting"""
    if level not in ["debug", "verbose", "info", "warn", "error"]:
        raise ValueError("Log level must be 'debug', 'verbose', 'info', 'warn', or 'error'")
    config = load_config()
    config.log_level = level
    save_config(config)