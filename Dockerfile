FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/

COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

COPY config/config-template.json ./config/config-template.json
COPY config/database-template.db ./config/database-template.db

RUN mkdir -p /app/downloads /app/config

ENV PYTHONPATH=/app

EXPOSE 58888

CMD ["python", "-m", "app.main"]
