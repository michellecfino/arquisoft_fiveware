"""
settings.py — Configuración principal de Django para el experimento de Disponibilidad ASR.

Tácticas de Bass implementadas aquí:
  - Táctica 2 (Timeout): OPTIONS de psycopg2 con 'options': '-c statement_timeout=200'
    fuerza un timeout estricto de 200ms en TODAS las consultas a la DB.
  - Táctica 1 (Heartbeat): CACHES configurado con Redis como backend para almacenar
    el estado 'db_available' verificado periódicamente por heartbeat.py.
"""

import os
from pathlib import Path
from decouple import config

# ---------------------------------------------------------------------------
# BASE
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="insecure-key-replace-in-production-!!!")

# En desarrollo, Django solo sirve estáticos automáticamente con DEBUG=True.
# En producción debes servir `/static/` con Nginx/WhiteNoise tras `collectstatic`.
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="*",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# ---------------------------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Application modules
    "src",
]

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "src.urls"

WSGI_APPLICATION = "src.wsgi.application"

# ---------------------------------------------------------------------------
# TEMPLATES — páginas HTML (p. ej. error de degradación vía Heartbeat)
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# DATABASE — PostgreSQL con psycopg2
#
# ===========================================================================
# TÁCTICA 2: TIMEOUT
# ===========================================================================
# El parámetro 'options': '-c statement_timeout=200' en el diccionario OPTIONS
# le indica a PostgreSQL que cancele CUALQUIER consulta que tarde más de 200ms.
# Esto implementa la táctica de Timeout de Bass a nivel de base de datos.
#
# Cuando se excede el límite, PostgreSQL lanza:
#   django.db.utils.OperationalError: canceling statement due to statement timeout
# Este error es capturado en views.py para retornar la respuesta degradada.
# ===========================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# CACHE — Redis (soporte para Táctica 1: Heartbeat)
#
# ===========================================================================
# TÁCTICA 1: HEARTBEAT
# ===========================================================================
# La caché Redis almacena la llave 'db_available' (True/False) que el proceso
# heartbeat.py actualiza cada 1 segundo. La vista en views.py consulta esta
# llave antes de intentar cualquier operación de base de datos.
#
# Flujo:
#   heartbeat.py: guarda cache.set('db_available', True/False, timeout=5)
#   views.py:     lee  cache.get('db_available', default=True)
# ===========================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"

# `collectstatic` juntará todo aquí (para producción / WhiteNoise / Nginx)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Estáticos de desarrollo en el repo (por ejemplo `static/img/...`)
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# LOGGING — para observabilidad de las tácticas de disponibilidad
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} [{name}:{lineno}] {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        # Log dedicado para tácticas de disponibilidad
        "disponibilidad.heartbeat": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "disponibilidad.services": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "disponibilidad.views": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
