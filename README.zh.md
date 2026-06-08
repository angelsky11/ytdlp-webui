# yt-dlp Web UI

[English](README.md)

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的现代化 Web 界面，用于从 YouTube 及其他平台下载视频。采用 React + Python FastAPI 构建，支持实时进度追踪、多语言界面和简洁的响应式 UI。

![Version](https://img.shields.io/badge/version-0.0.1--alpha-blue)
![Tech Stack](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Tech Stack](https://img.shields.io/badge/Python-FastAPI-009688?logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 截图

*(即将添加)*

---

## 功能特性

- **视频下载** — 支持 YouTube、Bilibili、Twitch 等 1000+ 网站
- **仅音频模式** — 下载最佳音质并转换为 MP3（192kbps）
- **视频质量选择** — 下载前选择分辨率
- **实时进度** — 通过 WebSocket 推送，无需轮询
- **多语言界面**（中文 / English）
- **任务管理** — 查看、取消、重试和删除下载任务
- **文件管理** — 浏览文件，支持缩略图预览
- **NFO 元数据生成** — 兼容 Emby/Jellyfin/Kodi
- **缩略图自动转换**（WebP → JPG）
- **Cookies 支持** — 导入浏览器 Cookies 访问受限内容
- **yt-dlp 版本管理** — 稳定版与 Nightly 版切换

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite 8 + Ant Design 6 + Zustand + React Router 7 |
| 后端 | Python 3 + FastAPI + SQLAlchemy + yt-dlp + WebSocket |
| 数据库 | SQLite（本地存储，零配置） |
| 部署 | Docker / Docker Compose（Windows / Linux / macOS） |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation)（可自动管理，但系统预装可加快首次启动）

### 开发模式

```bash
# 克隆仓库
git clone https://github.com/angelsky11/ytdlp-webui.git
cd ytdlp-webui

# Windows（双击或运行）
start.bat

# Linux/macOS
chmod +x start.sh
./start.sh
```

浏览器访问 **http://localhost:58888**。

> **注：** 首次启动可能需要一些时间来安装 Python 依赖和构建前端。

### Docker

```bash
docker compose up -d
```

---

## 项目结构

```
ytdlp-webui/
├── backend/                # Python FastAPI 后端
│   └── app/
│       ├── api/            # REST API 路由
│       ├── models/         # 数据库模型与 Schema
│       └── services/       # 下载管理器与 yt-dlp 集成
├── frontend/               # React + Vite 前端
│   └── src/
│       ├── components/     # UI 组件
│       ├── pages/          # 路由页面
│       ├── locales/        # 国际化翻译文件
│       ├── stores/         # Zustand 状态管理
│       └── api/            # API 客户端
├── config/                 # 运行时配置与数据（自动创建）
├── downloads/              # 下载文件（自动创建）
├── docker-compose.yml
└── Dockerfile
```

---

## 配置

通过 Web 界面 **设置** 页面进行配置：

| 配置项 | 说明 |
|--------|------|
| 默认格式 | 输出容器格式（mp4 / mkv） |
| yt-dlp 版本 | 稳定版或 Nightly 版 |
| Cookies | 上传浏览器 Cookies 以访问受限内容 |
| 日志级别 | Debug / Verbose / Info / Warn / Error |
| 语言 | 中文 / English |

---

## API

后端提供 `/api/` 前缀的 REST API，以及 `/api/ws` 的 WebSocket 端点用于实时进度推送。

### 主要端点

- `GET /api/health` — 健康检查
- `POST /api/downloads/` — 创建下载任务
- `GET /api/downloads/` — 获取所有任务列表
- `DELETE /api/downloads/{task_id}/remove` — 删除任务及关联文件
- `GET /api/files/` — 获取已下载文件列表
- `GET /api/config` — 获取应用配置

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)。

---

## 链接

- GitHub: [angelsky11/ytdlp-webui](https://github.com/angelsky11/ytdlp-webui)
- Telegram: [@angelsky11](https://t.me/angelsky11)
- yt-dlp: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
