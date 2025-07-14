#!/bin/bash

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

# Run Django migrations
echo "Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start supervisor
echo "Starting supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
