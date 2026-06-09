# yt-dlp Web UI

[中文](README.zh.md)

A modern web interface for downloading videos from YouTube and other platforms using [yt-dlp](https://github.com/yt-dlp/yt-dlp). Built with React and Python FastAPI, featuring real-time progress tracking, multi-language support, and a clean responsive UI.

![Version](https://img.shields.io/badge/version-0.0.1--alpha-blue)
![Tech Stack](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Tech Stack](https://img.shields.io/badge/Python-FastAPI-009688?logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Screenshots

*(Coming soon)*

---

## Features

- **Download videos** from YouTube, Bilibili, Twitch and 1000+ sites supported by yt-dlp
- **Audio-only mode** — downloads best quality audio and converts to MP3 (192kbps)
- **Video quality selection** — choose from available resolutions before downloading
- **Real-time progress** via WebSocket push (no polling)
- **Multi-language interface** (English / 中文)
- **Task management** — view, cancel, retry, and delete download tasks
- **File management** — browse downloaded files with thumbnail previews
- **NFO metadata generation** — Emby/Jellyfin/Kodi compatible .nfo files
- **Automatic thumbnail conversion** (WebP → JPG)
- **Cookies support** — import browser cookies for age-restricted content
- **yt-dlp version management** — switch between stable and nightly builds

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite 8 + Ant Design 6 + Zustand + React Router 7 |
| Backend  | Python 3 + FastAPI + SQLAlchemy + yt-dlp + WebSocket |
| Database | SQLite (local, zero-configuration) |
| Deployment | Docker / Docker Compose (Windows, Linux, macOS) |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation) (auto-managed, but system install can speed up first run)

### Local Development

```bash
# Clone the repository
git clone https://github.com/angelsky11/ytdlp-webui.git
cd ytdlp-webui

# Windows (double-click or run)
start.bat

# Linux/macOS
chmod +x start.sh
./start.sh
```

Access **http://localhost:58888** in your browser.

> **Note:** The first startup may take a moment as it installs Python dependencies and builds the frontend.

### Docker

**Docker Hub:** [angelsky11/ytdlp-webui](https://hub.docker.com/r/angelsky11/ytdlp-webui)

```bash
# 使用 Docker Hub 镜像（推荐）
docker run -d -p 58888:58888 -v ./downloads:/downloads -v ./config:/config angelsky11/ytdlp-webui:latest

# 或使用 docker-compose
docker compose up -d
```

---

## Project Structure

```
ytdlp-webui/
├── backend/                # Python FastAPI backend
│   └── app/
│       ├── api/            # REST API routes
│       ├── models/         # Database models & schemas
│       └── services/       # Download manager & yt-dlp integration
├── frontend/               # React + Vite frontend
│   └── src/
│       ├── components/     # UI components
│       ├── pages/          # Route pages
│       ├── locales/        # i18n translation files
│       ├── stores/         # Zustand state management
│       └── api/            # API client
├── config/                 # Runtime config & data (auto-created)
├── downloads/              # Downloaded files (auto-created)
├── docker-compose.yml
└── Dockerfile
```

---

## Configuration

Settings are available through the web UI at **Settings** page:

| Setting | Description |
|---------|-------------|
| Default Format | Output container format (mp4 / mkv) |
| yt-dlp Version | Stable or Nightly build |
| Cookies | Upload browser cookies for restricted content |
| Log Level | Debug / Verbose / Info / Warn / Error |
| Language | English / 中文 |

---

## API

The backend exposes REST API under `/api/` prefix and a WebSocket endpoint at `/api/ws` for real-time progress updates.

### Main Endpoints

- `GET /api/health` — Health check
- `POST /api/downloads/` — Create a new download task
- `GET /api/downloads/` — List all download tasks
- `DELETE /api/downloads/{task_id}/remove` — Remove a task and its files
- `GET /api/files/` — List downloaded files
- `GET /api/config` — Get application configuration

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Links

- GitHub: [angelsky11/ytdlp-webui](https://github.com/angelsky11/ytdlp-webui)
- Telegram: [@angelsky11](https://t.me/angelsky11)
- yt-dlp: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
