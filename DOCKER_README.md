# Online Judge - Docker Deployment Guide

## Overview

This guide provides step-by-step instructions for containerizing and deploying the Online Judge platform using Docker and Docker Compose.

## Architecture

The dockerized application consists of:
- **Django Web Server**: Main application server
- **Celery Worker**: Background task processing for code evaluation
- **Redis**: Message broker and result backend
- **Supervisor**: Process manager to run multiple services in one container

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)
- At least 2GB RAM available for containers

## Quick Start

### Option 1: Using Deployment Scripts

**For Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**For Windows (PowerShell):**
```powershell
.\deploy.ps1
```

### Option 2: Manual Deployment

1. **Build and start services:**
```bash
docker-compose up --build -d
```

2. **Check service status:**
```bash
docker-compose ps
```

3. **View logs:**
```bash
docker-compose logs -f
```

## Project Structure

```
Online_Judge/
├── Dockerfile                 # Multi-stage production Dockerfile
├── docker-compose.yml        # Service orchestration
├── supervisord.conf          # Process management configuration
├── entrypoint.sh             # Container startup script
├── requirements.txt          # Python dependencies
├── deploy.sh                 # Linux/macOS deployment script
├── deploy.ps1                # Windows deployment script
└── .dockerignore             # Files to exclude from Docker build
```

## Key Features

### Multi-Service Architecture
- **Django**: Runs on port 8000 (exposed)
- **Celery**: Background worker for code evaluation
- **Redis**: Message broker on port 6379 (exposed)

### Security Features
- Non-root user execution
- Network isolation for code execution
- Docker-in-Docker for secure code evaluation

### Production Optimizations
- Multi-stage build for smaller image size
- Proper logging configuration
- Health checks for services
- Automatic service restart on failure

## Configuration

### Environment Variables

The application uses the following environment variables:

```bash
DJANGO_SETTINGS_MODULE=Online_Judge.settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Volumes

- `redis_data`: Persistent Redis data storage
- `/var/run/docker.sock`: Docker socket for code execution

## Service Management

### Starting Services
```bash
docker-compose up -d
```

### Stopping Services
```bash
docker-compose down
```

### Restarting Services
```bash
docker-compose restart
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f redis
```

### Accessing Django Shell
```bash
docker-compose exec web python manage.py shell
```

### Running Django Commands
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check which process is using port 8000
   lsof -i :8000
   # Kill the process or change port in docker-compose.yml
   ```

2. **Redis Connection Error**
   ```bash
   # Check Redis container status
   docker-compose ps redis
   # View Redis logs
   docker-compose logs redis
   ```

3. **Celery Worker Not Starting**
   ```bash
   # Check Celery logs
   docker-compose logs web | grep celery
   # Restart services
   docker-compose restart
   ```

### Debugging

1. **Access container shell:**
```bash
docker-compose exec web /bin/bash
```

2. **Check process status inside container:**
```bash
docker-compose exec web supervisorctl status
```

3. **View detailed logs:**
```bash
# Django logs
docker-compose exec web tail -f /var/log/django/django.log

# Celery logs
docker-compose exec web tail -f /var/log/celery/celery.log
```

## Production Deployment

### For AWS ECR and EC2 Deployment

1. **Tag the image:**
```bash
docker tag online-judge:latest <account-id>.dkr.ecr.<region>.amazonaws.com/online-judge:latest
```

2. **Push to ECR:**
```bash
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/online-judge:latest
```

3. **Deploy on EC2:**
```bash
# On EC2 instance
docker pull <account-id>.dkr.ecr.<region>.amazonaws.com/online-judge:latest
docker run -d -p 8000:8000 <account-id>.dkr.ecr.<region>.amazonaws.com/online-judge:latest
```

### Environment-Specific Configurations

- Update `ALLOWED_HOSTS` in `settings.py` for production domains
- Configure proper database for production (PostgreSQL recommended)
- Set up proper logging and monitoring
- Configure SSL/TLS certificates

## Monitoring

### Health Checks
```bash
# Check if services are healthy
docker-compose ps

# Test Django endpoint
curl http://localhost:8000/

# Test Redis connection
redis-cli -h localhost -p 6379 ping
```

### Resource Usage
```bash
# Monitor container resource usage
docker stats
```

## Backup and Restore

### Database Backup
```bash
docker-compose exec web python manage.py dumpdata > backup.json
```

### Database Restore
```bash
docker-compose exec web python manage.py loaddata backup.json
```

## Development vs Production

### Development Mode
- Use the current setup with volume mounts
- Enable Django debug mode
- Use development database (SQLite)

### Production Mode
- Remove volume mounts
- Disable Django debug mode
- Use production database (PostgreSQL)
- Configure proper logging
- Set up monitoring and alerting

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review container logs
3. Verify all services are running
4. Check network connectivity between containers

## License

This project is licensed under the MIT License.


## USE FULL COMMANDS:
```
docker build -t online-judge:latest .
docker compose down;docker compose up -d
```
should be applied in the PS I:\Online_Judge> folder of the terminal