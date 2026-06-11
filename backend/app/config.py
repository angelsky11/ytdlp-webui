from pathlib import Path
import os

# APP_DIR is two levels up from this file (backend/app/)
APP_DIR = Path(__file__).resolve().parent.parent

# Determine BASE_DIR based on environment
# In Docker: APP_DIR = /app, and /app/frontend exists
# In development: APP_DIR = /path/to/project/backend, and /path/to/project/frontend exists
if os.path.exists(APP_DIR / "frontend"):
    # Docker environment - APP_DIR is /app
    BASE_DIR = APP_DIR
elif os.path.exists(APP_DIR.parent / "frontend"):
    # Development environment - go one more level up
    BASE_DIR = APP_DIR.parent
else:
    # Fallback to APP_DIR if neither exists
    BASE_DIR = APP_DIR

DOWNLOAD_DIR = Path(os.environ.get('DOWNLOAD_DIR', BASE_DIR / "downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_DIR = Path(os.environ.get('CONFIG_DIR', BASE_DIR / "config"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.environ.get('PORT', 58888))