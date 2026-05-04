from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = ["*"] # Para despliegue en EC2

# --- APLICACIONES ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "logs",  # <--- Debe llamarse como la carpeta de la app que creamos
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

# CRUCIAL: Cambiar "manejador_reportes" por "manejador_logs"
ROOT_URLCONF = "manejador_logs.urls"

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

# CRUCIAL: Cambiar "manejador_reportes" por "manejador_logs"
WSGI_APPLICATION = "manejador_logs.wsgi.application"

# --- CONFIGURACIÓN DE BASES DE DATOS ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("AUDIT_DB_NAME", "postgres"),
        "USER": os.getenv("AUDIT_DB_USER", "postgres"),
        "PASSWORD": os.getenv("AUDIT_DB_PASSWORD", "postgres123"),
        "HOST": os.getenv("AUDIT_DB_HOST", "audit-db.c4mxolen2vp8.us-east-1.rds.amazonaws.com"),
        "PORT": os.getenv("AUDIT_DB_PORT", "5432"),
    }
}

# Al ser un microservicio dedicado, la RDS de auditoría es su "default".
# No necesitas el multi-db complejo aquí porque este server SOLO hace logs.

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota" # Ajustado a tu zona horaria
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
