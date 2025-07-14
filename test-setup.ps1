# Test Docker setup for Online Judge

Write-Host "🧪 Testing Docker setup for Online Judge" -ForegroundColor Green

# Test 1: Check if Docker is installed and running
Write-Host "📋 Test 1: Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
    exit 1
}

# Test 2: Check if Docker Compose is available
Write-Host "📋 Test 2: Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose is available: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not available" -ForegroundColor Red
    exit 1
}

# Test 3: Check if required files exist
Write-Host "📋 Test 3: Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "supervisord.conf",
    "entrypoint.sh",
    "manage.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file is missing" -ForegroundColor Red
        exit 1
    }
}

# Test 4: Validate Docker Compose file
Write-Host "📋 Test 4: Validating Docker Compose file..." -ForegroundColor Yellow
try {
    docker-compose config | Out-Null
    Write-Host "✅ Docker Compose file is valid" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose file has errors" -ForegroundColor Red
    exit 1
}

# Test 5: Check available ports
Write-Host "📋 Test 5: Checking if ports are available..." -ForegroundColor Yellow
$ports = @(8000, 6379)
foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet
    if ($connection) {
        Write-Host "⚠️  Port $port is already in use" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Port $port is available" -ForegroundColor Green
    }
}

Write-Host "🎉 All tests passed! Ready for deployment." -ForegroundColor Green
Write-Host "Run '.\deploy.ps1' to start the application." -ForegroundColor Cyan
