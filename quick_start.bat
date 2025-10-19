@echo off
echo 🚀 Quick Starting SuperTickets.AI...
echo.

echo Starting containers...
docker-compose up -d

echo.
echo Waiting 10 seconds for startup...
timeout /t 10 /nobreak > nul

echo.
echo Checking status...
docker-compose ps

echo.
echo Testing backend...
curl -f http://localhost:8000/health

echo.
echo ✅ Done! Check http://localhost:3000 for frontend
pause