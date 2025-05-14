@echo off
echo Setting up Learnyst Automation External Service...
echo.

REM Check if Docker is installed
docker --version > nul 2>&1
if %errorlevel% neq 0 (
  echo Docker is not installed or not in PATH. Please install Docker Desktop first.
  pause
  exit /b
)

REM Start Docker Compose
echo Starting Docker services...
docker-compose up -d

echo.
echo Setup complete! The external service is running at http://10.0.0.77:5500
echo.
echo You can check the logs with: docker-compose logs -f
echo.
pause