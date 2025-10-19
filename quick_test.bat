@echo off
echo 🚀 Quick Test of SuperTickets.AI Core System
echo.

echo Starting services...
docker-compose up -d

echo.
echo Waiting 20 seconds for startup...
timeout /t 20 /nobreak > nul

echo.
echo Container status:
docker-compose ps

echo.
echo Testing backend...
python test_backend_health.py

echo.
pause