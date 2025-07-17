#!/usr/bin/env python
"""
Debug script to test Django installation and basic functionality
"""
import os
import sys

def check_django():
    try:
        import django
        print(f"✅ Django is installed - Version: {django.get_version()}")
        return True
    except ImportError:
        print("❌ Django is not installed")
        return False

def check_environment():
    print("🔍 Environment Variables:")
    print(f"   DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")
    print(f"   CELERY_BROKER_URL: {os.environ.get('CELERY_BROKER_URL', 'Not set')}")
    print(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

def check_settings():
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Online_Judge.settings')
        import django
        django.setup()
        
        from django.conf import settings
        print(f"✅ Django settings loaded successfully")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"   DATABASE: {settings.DATABASES['default']['ENGINE']}")
        return True
    except Exception as e:
        print(f"❌ Failed to load Django settings: {e}")
        return False

def check_urls():
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        print("✅ URL patterns loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load URL patterns: {e}")
        return False

def main():
    print("🚀 Django Setup Debug Script")
    print("=" * 40)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check current directory
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check if manage.py exists
    if os.path.exists('manage.py'):
        print("✅ manage.py found")
    else:
        print("❌ manage.py not found")
    
    # Check environment
    check_environment()
    
    # Check Django installation
    if not check_django():
        return
    
    # Check Django settings
    if not check_settings():
        return
    
    # Check URL patterns
    check_urls()
    
    print("=" * 40)
    print("🎉 All checks completed!")

if __name__ == '__main__':
    main()
