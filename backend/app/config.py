from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DOWNLOAD_DIR = Path(os.environ.get('DOWNLOAD_DIR', BASE_DIR / "downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_DIR = Path(os.environ.get('CONFIG_DIR', BASE_DIR / "config"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.environ.get('PORT', 58888))