@echo off
echo ==============================
echo Online Judge Docker Setup
echo ==============================

REM Stop existing containers
echo Stopping existing containers...
docker-compose down

REM Build the image
echo Building Docker image...
docker build -t online-judge:latest .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed!
    exit /b 1
)

REM Start the services
echo Starting services...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ❌ Docker compose up failed!
    exit /b 1
)

echo ✅ Services started successfully!

REM Wait a bit for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo Checking service status...
docker-compose ps

REM Test if web service is responsive
echo Testing web service...
docker-compose exec web python test_docker_judge.py

if %errorlevel% equ 0 (
    echo ✅ Docker-in-Docker judge system is working!
) else (
    echo ❌ Docker-in-Docker judge system test failed!
    echo Check logs with: docker-compose logs web
)

echo ==============================
echo Setup complete!
echo Access the application at: http://localhost:8000
echo View logs with: docker-compose logs -f web
echo ==============================
pause
