@echo off
echo 🔧 Fixing SuperTickets.AI Backend...
echo.

echo Step 1: Stopping all containers...
docker-compose down

echo.
echo Step 2: Removing old images...
docker-compose down --rmi all --volumes --remove-orphans

echo.
echo Step 3: Rebuilding with no cache...
docker-compose build --no-cache

echo.
echo Step 4: Starting services...
docker-compose up -d

echo.
echo Step 5: Waiting for services to start...
timeout /t 10 /nobreak > nul

echo.
echo Step 6: Checking status...
docker-compose ps

echo.
echo Step 7: Testing backend...
curl -f http://localhost:8000/health

echo.
echo ✅ Fix complete! 
echo.
echo Check these URLs:
echo   🌐 Frontend: http://localhost:3000
echo   🔧 Backend:  http://localhost:8000/health
echo.
echo If still not working, check logs with:
echo   docker-compose logs supertickets-ai
echo.
pause