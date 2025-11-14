"""
ASGI config for Pozinox project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Pozinox.settings')
application = get_asgi_application()
