@echo off
echo 🚀 Starting SuperTickets.AI and Testing...
echo.

echo Starting services...
docker-compose up -d

echo.
echo Waiting 30 seconds for startup...
timeout /t 30 /nobreak > nul

echo.
echo Checking container status...
docker-compose ps

echo.
echo Testing backend health...
python -c "
import requests
try:
    response = requests.get('http://localhost:8000/health', timeout=10)
    if response.status_code == 200:
        print('✅ Backend is healthy:', response.json())
    else:
        print('❌ Backend returned status:', response.status_code)
except Exception as e:
    print('❌ Backend connection failed:', e)
"

echo.
echo Testing email monitoring endpoints...
python test_email_monitoring.py

echo.
echo ✅ Test complete!
pause