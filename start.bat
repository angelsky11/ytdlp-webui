@echo off

echo Building frontend...
cd frontend
call npm install
call npm run build
cd ..

echo Starting server on port 58888...
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 58888