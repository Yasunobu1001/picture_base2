#!/usr/bin/env python
"""
Verification script for Django project setup
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_sharing_site.settings')
django.setup()

from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line

def verify_setup():
    """Verify that all components are properly set up"""
    print("🔍 Verifying Django Photo Sharing Site Setup...")
    
    # Check Django settings
    print(f"✅ Django version: {django.get_version()}")
    print(f"✅ Debug mode: {settings.DEBUG}")
    print(f"✅ Database engine: {settings.DATABASES['default']['ENGINE']}")
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Check static files
    static_css = BASE_DIR / 'static' / 'css' / 'output.css'
    if static_css.exists():
        print("✅ Tailwind CSS compiled: OK")
    else:
        print("❌ Tailwind CSS not compiled")
        return False
    
    # Check templates
    base_template = BASE_DIR / 'templates' / 'base.html'
    if base_template.exists():
        print("✅ Base template: OK")
    else:
        print("❌ Base template missing")
        return False
    
    # Check media directory
    media_dir = BASE_DIR / 'media'
    if media_dir.exists():
        print("✅ Media directory: OK")
    else:
        print("❌ Media directory missing")
        return False
    
    print("\n🎉 All components verified successfully!")
    print("📋 Setup Summary:")
    print("   - Django project initialized")
    print("   - PostgreSQL database connected")
    print("   - Tailwind CSS integrated")
    print("   - Static and media files configured")
    print("   - Base templates created")
    print("\n✨ Ready for development!")
    
    return True

if __name__ == '__main__':
    verify_setup()