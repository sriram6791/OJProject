#!/bin/bash
set -e

echo "Starting Django application setup..."

# Fix Docker socket permissions if it exists
if [ -e /var/run/docker.sock ]; then
    echo "Setting Docker socket permissions..."
    chmod 666 /var/run/docker.sock
    ls -la /var/run/docker.sock
fi

# Create and set permissions for temp directory
echo "Creating temporary directory for code execution..."
mkdir -p /tmp/oj_submissions
chmod 777 /tmp/oj_submissions
echo "Temp directory created: $(ls -la /tmp/oj_submissions)"

# Check if Redis is available based on environment variable
if [[ -n "$CELERY_BROKER_URL" && "$CELERY_BROKER_URL" == *"redis://"* ]]; then
    # Extract host and port from CELERY_BROKER_URL
    REDIS_HOST=$(echo $CELERY_BROKER_URL | sed -E 's/redis:\/\/([^:]+):.*/\1/')
    REDIS_PORT=$(echo $CELERY_BROKER_URL | sed -E 's/redis:\/\/[^:]+:([0-9]+).*/\1/')
    
    echo "Checking Redis connection at $REDIS_HOST:$REDIS_PORT..."
    
    # Try to connect to Redis a few times
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while ! nc -z $REDIS_HOST $REDIS_PORT 2>/dev/null && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        echo "Waiting for Redis to be available... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
        sleep 1
        RETRY_COUNT=$((RETRY_COUNT+1))
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "WARNING: Redis not available after $MAX_RETRIES attempts, but continuing anyway..."
    else
        echo "Redis is ready!"
    fi
else
    echo "No Redis URL configured or not using Redis. Skipping Redis check."
fi

# Create log directories
echo "Creating log directories..."
mkdir -p /var/log/supervisor /var/log/celery /var/log/django

# Run Django migrations
echo "Running Django migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Setting up superuser..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

echo "Starting supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
