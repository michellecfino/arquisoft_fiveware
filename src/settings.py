"""
settings.py — Configuración principal de Django para el experimento de Disponibilidad ASR.

Tácticas de Bass implementadas aquí:
  - Táctica 2 (Timeout): OPTIONS de psycopg2 con 'options': '-c statement_timeout=1000'
    fuerza un timeout de 1000ms en las consultas PostgreSQL.
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

# Detrás de Kong / ALB (HTTP)
USE_X_FORWARDED_HOST = config("USE_X_FORWARDED_HOST", default=True, cast=bool)

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
# DATABASE — PostgreSQL (RDS) con fallback a SQLite local
#
# ===========================================================================
# TÁCTICA 2: TIMEOUT (1000ms)
# ===========================================================================
# statement_timeout=1000 → cualquier consulta que exceda 1s será cancelada
# por PostgreSQL y capturada para degradación (ASR <= 400ms para respuesta final,
# pero el timeout es la barrera de DB; la rama Heartbeat evita esperar ese segundo
# cuando la DB ya está caída).
# ===========================================================================

DB_HOST = config("DB_HOST", default="")
DB_PORT = config("DB_PORT", default="5432")
DB_NAME = config("DB_NAME", default="disponibilidad_db")
DB_USER = config("DB_USER", default="dbadmin")
DB_PASSWORD = config("DB_PASSWORD", default="12345678")

if DB_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": DB_HOST,
            "PORT": DB_PORT,
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "OPTIONS": {
                "options": "-c statement_timeout=1000",
            },
        }
    }
else:
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

REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/1")

# En EC2 usamos Redis local (instalado por user_data) para almacenar el heartbeat.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
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
