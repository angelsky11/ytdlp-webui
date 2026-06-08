from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import CONFIG_DIR
import os

os.makedirs(CONFIG_DIR, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(str(CONFIG_DIR), 'database.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DownloadTaskModel(Base):
    __tablename__ = "download_tasks"

    id = Column(String, primary_key=True, index=True)
    url = Column(String, index=True)
    status = Column(String, default="pending")
    filename = Column(String, nullable=True)
    title = Column(String, nullable=True)  # 视频标题（前端传递）
    progress = Column(Float, default=0.0)
    stage = Column(String, nullable=True)  # 当前阶段
    speed = Column(String, nullable=True)
    eta = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    format = Column(String, default="best")
    audio_only = Column(Boolean, default=False)
    output_template = Column(String, default="%(title)s.%(ext)s")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class DownloadedFileModel(Base):
    """下载完成后记录的文件信息，替代每次扫描文件系统"""
    __tablename__ = "downloaded_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True)
    path = Column(String, unique=True)
    size = Column(BigInteger, default=0)
    file_type = Column(String, default="other")  # video/thumbnail/json/audio/other
    group_key = Column(String, index=True)  # 用于分组（同视频的基础文件名）
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
