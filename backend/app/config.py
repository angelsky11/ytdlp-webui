from pathlib import Path
import os

# APP_DIR is two levels up from this file (backend/app/)
APP_DIR = Path(__file__).resolve().parent.parent

# Determine BASE_DIR:
# - In Docker: APP_DIR = /app (which is the project root)
# - In development: APP_DIR = /path/to/project/backend (need to go up one more level)
if os.path.exists(APP_DIR / "frontend"):
    # Docker environment - APP_DIR is already the project root
    BASE_DIR = APP_DIR
else:
    # Development environment - go one level up to get project root
    BASE_DIR = APP_DIR.parent

# Download and config directories are under BASE_DIR
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.environ.get('PORT', 58888))