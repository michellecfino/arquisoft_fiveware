from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = ["*"] if os.getenv("ALLOWED_HOSTS", "*") == "*" else os.getenv("ALLOWED_HOSTS").split(",")

# --- APLICACIONES ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reportes",        # App para el manejo de reportes
    "manejador_logs",  # App para el manejo de auditoría (logs)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "manejador_reportes.urls"

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

WSGI_APPLICATION = "manejador_reportes.wsgi.application"

# --- CONFIGURACIÓN DE BASES DE DATOS (MULTI-DB) ---
# Aquí separamos la lógica de Reportes de la de Auditoría
DATABASES = {
    # 1. Base de datos por defecto (para la App de Reportes)
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    },
    # 2. Base de datos de Auditoría (la RDS "escondida" en AWS)
    "audit_db": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("AUDIT_DB_NAME", "postgres"),
        "USER": os.getenv("AUDIT_DB_USER", "postgres"),
        "PASSWORD": os.getenv("AUDIT_DB_PASSWORD", "postgres123"),
        "HOST": os.getenv("AUDIT_DB_HOST", "audit-db.c4mxolen2vp8.us-east-1.rds.amazonaws.com"),
        "PORT": os.getenv("AUDIT_DB_PORT", "5432"),
    }
}

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = "es-co"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
