# Use Python 3.12 slim as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=Online_Judge.settings
ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jdk \
    supervisor \
    docker.io \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for logs and temp judge files
RUN mkdir -p /var/log/supervisor /var/log/celery /var/log/django /tmp/oj_submissions

# Set permissions for temp judge directory
RUN chmod -R 777 /tmp/oj_submissions

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Django port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]