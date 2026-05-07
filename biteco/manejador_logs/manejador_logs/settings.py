from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "audit-secret-key-123")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "3.80.36.86",       # La IP Pública de este servidor (Audit-Server)
    "172.31.20.28",     # La IP Privada de este servidor (Audit-Server)
    "3.91.97.197",      # La IP Pública de Reportes (por si acaso)
    "172.31.17.51",     # IP Privada Reportes 1
    "172.31.26.43",     # IP Privada Reportes 2
    "172.31.18.237",    # IP Privada Reportes 3
    "172.31.17.54",     # IP Privada Reportes 4
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "manejador_logs", # Tu app de auditoría
    "logs",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "manejador_logs.urls"

# ESTA ES LA BASE DE DATOS DE AUDITORÍA (RDS ESCONDIDA)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "postgres"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres123"),
        "HOST": os.getenv("DB_HOST", "audit-db.c4mxolen2vp8.us-east-1.rds.amazonaws.com"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
