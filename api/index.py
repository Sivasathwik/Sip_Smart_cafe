import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coffeshop.settings")

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

if os.environ.get("VERCEL"):
    call_command("migrate", interactive=False, verbosity=0)
    call_command("add_sample_menu", verbosity=0)

app = application
