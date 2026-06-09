FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends curl xz-utils && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Download prebuilt ffmpeg for Linux (amd64)
RUN mkdir -p /app/ffmpeg && \
    curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | \
    tar -xJ --wildcards -O '*/ffmpeg' > /app/ffmpeg/ffmpeg && \
    chmod +x /app/ffmpeg/ffmpeg && \
    ln -s /app/ffmpeg/ffmpeg /usr/local/bin/ffmpeg

COPY backend/app/ ./app/

COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

RUN mkdir -p /downloads /config

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "58888"]
