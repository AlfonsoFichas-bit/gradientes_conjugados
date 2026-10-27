"""Configuración de Django para el simulador presupuestario."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-change-me-9f3a7c1e5b8d2f4a6c0e",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1").strip().lower() not in {"0", "false", "no"}

_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
ALLOWED_HOSTS = ["*"] if _hosts.strip() == "*" else [h.strip() for h in _hosts.split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    origen.strip()
    for origen in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origen.strip()
]

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inertia",
    "simulador",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "inertia.middleware.InertiaMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# No se usan modelos: la sesión se guarda en una cookie firmada.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

LANGUAGE_CODE = "es-bo"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Inertia.js
INERTIA_LAYOUT = "app.html"
INERTIA_VERSION = os.environ.get("INERTIA_VERSION", "dev")
# El servidor de Vite se usa solo con DEBUG; en producción se lee el manifest.
VITE_DEV_SERVER = os.environ.get("VITE_DEV_SERVER", "http://127.0.0.1:5173")
VITE_ENTRY = "frontend/main.ts"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
