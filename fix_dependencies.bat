@echo off
echo 🔧 Fixing SuperTickets.AI Dependencies...
echo.

echo Step 1: Stopping containers...
docker-compose down

echo.
echo Step 2: Cleaning up old images...
docker system prune -f

echo.
echo Step 3: Installing dependencies locally (for testing)...
pip install --upgrade pip
pip install fastapi uvicorn pydantic supabase python-dotenv httpx

echo.
echo Step 4: Rebuilding with simple requirements...
docker-compose build --no-cache --build-arg REQUIREMENTS_FILE=requirements-simple.txt

echo.
echo Step 5: Starting services...
docker-compose up -d

echo.
echo Step 6: Checking status...
timeout /t 15 /nobreak > nul
docker-compose ps

echo.
echo Step 7: Testing backend...
curl -f http://localhost:8000/health

echo.
echo ✅ Dependencies fixed!
echo.
echo If still having issues, try:
echo   1. pip install -r requirements-simple.txt
echo   2. python -m mcp_service.main
echo.
pause