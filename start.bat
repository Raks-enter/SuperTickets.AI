@echo off
echo Starting SuperTickets.AI...
echo.

echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and make sure it's running
    pause
    exit /b 1
)

echo Building and starting services...
docker-compose up -d

echo.
echo ✅ SuperTickets.AI is starting up!
echo.
echo Services will be available at:
echo   🌐 Web Dashboard: http://localhost:3000
echo   🔧 Backend API:   http://localhost:8000
echo   📊 Grafana:       http://localhost:3001
echo.
echo To check status: docker-compose ps
echo To view logs:    docker-compose logs -f
echo To stop:         docker-compose down
echo.
pause