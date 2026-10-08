@echo off
echo Starting Backend (FastAPI)...
start cmd /k "cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo Starting Frontend (React/Vite)...
start cmd /k "cd frontend && npm run dev"

echo.
echo Application started!
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo.
pause
