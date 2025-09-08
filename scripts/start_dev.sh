#!/bin/bash

# Development startup script for Selenium Automation Backend

echo "Starting Selenium Automation Backend in development mode..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser (if not exists)..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A automation_backend worker -l info &
CELERY_PID=$!

# Start Django development server
echo "Starting Django development server..."
echo "=========================================="
echo "Application URLs:"
echo "  Admin: http://localhost:8000/admin/"
echo "  API: http://localhost:8000/api/"
echo "  Username: admin"
echo "  Password: admin123"
echo "=========================================="

python manage.py runserver

# Cleanup on exit
echo "Shutting down..."
kill $CELERY_PID 2>/dev/null
