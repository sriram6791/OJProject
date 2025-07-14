# PowerShell Build and deployment script for Online Judge

Write-Host "🚀 Starting Online Judge Docker Build & Deployment" -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Clean up any existing containers
Write-Host "🧹 Cleaning up existing containers..." -ForegroundColor Yellow
docker-compose down --volumes --remove-orphans

# Build the Docker image
Write-Host "🏗️  Building Docker image..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start the services
Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Yellow
docker-compose ps

# Show logs
Write-Host "📋 Recent logs:" -ForegroundColor Yellow
docker-compose logs --tail=50

Write-Host "✅ Deployment completed!" -ForegroundColor Green
Write-Host "🌐 Online Judge is running at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 Redis is running at: localhost:6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs: docker-compose logs -f"
Write-Host "  Stop services: docker-compose down"
Write-Host "  Restart services: docker-compose restart"
Write-Host "  Access Django shell: docker-compose exec web python manage.py shell"
