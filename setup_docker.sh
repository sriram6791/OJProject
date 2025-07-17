#!/bin/bash

echo "=============================="
echo "Online Judge Docker Setup"
echo "=============================="

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Remove existing containers and volumes (optional - uncomment if needed)
# echo "Removing existing containers and volumes..."
# docker-compose down -v
# docker system prune -f

# Build the image
echo "Building Docker image..."
docker build -t online-judge:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

# Start the services
echo "Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Docker compose up failed!"
    exit 1
fi

echo "✅ Services started successfully!"

# Wait a bit for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "Checking service status..."
docker-compose ps

# Test if web service is responsive
echo "Testing web service..."
if docker-compose exec web python test_docker_judge.py; then
    echo "✅ Docker-in-Docker judge system is working!"
else
    echo "❌ Docker-in-Docker judge system test failed!"
    echo "Check logs with: docker-compose logs web"
fi

echo "=============================="
echo "Setup complete!"
echo "Access the application at: http://localhost:8000"
echo "View logs with: docker-compose logs -f web"
echo "=============================="
