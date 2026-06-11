from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models.database import init_db
from app.config import PORT
import os

# 导入日志模块
from app.logger import app_logger

# 立即初始化数据库表（模型类已在 database.py 中注册到 Base.metadata）
init_db()

# 导入 API 路由（此时数据库表已存在，DownloadManager 初始化时不会报错）
from app.api import downloads, files, config

# 初始化 DownloadManager（它需要查询 DB）
from app.services.downloader import download_manager
from app.models.schemas import DownloadProgress

# 记录启动日志
app_logger.info("Application starting...")

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