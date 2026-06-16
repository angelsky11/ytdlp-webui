from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import PORT
import os
import traceback

# 导入日志模块
from app.logger import app_logger

# 初始化数据库和配置（在导入 download_manager 之前）
from app.config_manager import init_config_from_template, init_database_from_template

app_logger.info("Initializing config from template...")
init_config_from_template()

app_logger.info("Initializing database from template...")
init_database_from_template()

# 导入 API 路由
from app.api import downloads, files, config

# 初始化 DownloadManager（它需要查询 DB）
from app.services.downloader import download_manager
from app.models.schemas import DownloadProgress

# 记录启动日志
app_logger.info("="*60)
app_logger.info("ytdlp-webui starting...")
app_logger.info("="*60)

app = FastAPI(
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes with /api prefix
app.include_router(downloads.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(config.router, prefix="/api")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


async def websocket_progress_callback(progress: DownloadProgress):
    await manager.broadcast(progress.model_dump_json())


download_manager.add_progress_callback(websocket_progress_callback)


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


# Frontend static files path - use absolute path from app root
from app.config import BASE_DIR
FRONTEND_DIST = os.path.join(str(BASE_DIR), "frontend", "dist")


# Mount assets directory for JS/CSS files
assets_dir = os.path.join(FRONTEND_DIST, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


# Serve static files (favicon, icons, etc.)
@app.get("/favicon.svg")
async def favicon():
    file_path = os.path.join(FRONTEND_DIST, "favicon.svg")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


@app.get("/icons.svg")
async def icons():
    file_path = os.path.join(FRONTEND_DIST, "icons.svg")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


# Catch-all route for SPA - must be last
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Serve index.html for all non-API routes (SPA routing)"""
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


# Global exception handlers for better error logging
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    app_logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    app_logger.error(f"Request URL: {request.url}")
    app_logger.error(f"Request method: {request.method}")
    raise exc


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    app_logger.error(f"Validation Error: {exc.errors()}")
    app_logger.error(f"Request URL: {request.url}")
    app_logger.error(f"Request method: {request.method}")
    app_logger.error(f"Body: {await request.body()}")
    raise exc


if __name__ == "__main__":
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    from app.config_manager import ensure_all_dependencies
    
    # 初始化所有依赖工具（yt-dlp, ffmpeg, deno）
    app_logger.info("Initializing application dependencies...")
    ensure_all_dependencies()
    
    # Override uvicorn logging format to include timestamp
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        log_config=LOGGING_CONFIG
    )