# Plantilla de archivo WSGI para PythonAnywhere.
# Copia este contenido en el archivo WSGI que crea PythonAnywhere
# (Web tab -> "WSGI configuration file"), reemplazando <usuario>.

import os
import sys

USUARIO = "<usuario>"
RUTA_PROYECTO = f"/home/{USUARIO}/gradientes_conjugados"

if RUTA_PROYECTO not in sys.path:
    sys.path.insert(0, RUTA_PROYECTO)

# --- Variables de entorno de produccion ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_DEBUG", "0")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", f"{USUARIO}.pythonanywhere.com")
os.environ.setdefault(
    "DJANGO_CSRF_TRUSTED_ORIGINS", f"https://{USUARIO}.pythonanywhere.com"
)
# Genera una clave con: python -c "import secrets; print(secrets.token_urlsafe(50))"
os.environ.setdefault("DJANGO_SECRET_KEY", "REEMPLAZA_CON_UNA_CLAVE_LARGA_Y_ALEATORIA")
# os.environ.setdefault("NOMBRE_ESTUDIANTE", "Tu Nombre")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
