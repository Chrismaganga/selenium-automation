#!/usr/bin/env python3
"""
Setup script for the Selenium Automation Backend
"""
import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def setup_environment():
    """Set up the development environment"""
    print("Setting up Selenium Automation Backend...")
    
    # Create necessary directories
    directories = ['media', 'media/screenshots', 'media/html', 'media/captcha_screenshots', 'logs', 'staticfiles']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automation_backend.settings')
    django.setup()
    
    # Run migrations
    if not run_command("python manage.py makemigrations", "Creating database migrations"):
        return False
    
    if not run_command("python manage.py migrate", "Running database migrations"):
        return False
    
    # Create superuser
    print("Creating superuser account...")
    try:
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("✓ Superuser created (username: admin, password: admin123)")
        else:
            print("✓ Superuser already exists")
    except Exception as e:
        print(f"✗ Failed to create superuser: {e}")
    
    # Collect static files
    if not run_command("python manage.py collectstatic --noinput", "Collecting static files"):
        return False
    
    print("\n" + "="*50)
    print("Setup completed successfully!")
    print("="*50)
    print("\nTo start the application:")
    print("1. Start Redis: docker run -p 6379:6379 -d redis:7")
    print("2. Start Celery worker: celery -A automation_backend worker -l info")
    print("3. Start Django server: python manage.py runserver")
    print("\nAdmin interface: http://localhost:8000/admin/")
    print("API documentation: http://localhost:8000/api/")
    print("="*50)

if __name__ == "__main__":
    setup_environment()
