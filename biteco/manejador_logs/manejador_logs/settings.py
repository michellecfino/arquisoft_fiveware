from pathlib import Path
import os
import boto3  # <--- IMPORTANTE: Agrégalo aquí
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "audit-secret-key-123")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "3.80.36.86",       # La IP Pública de este servidor (Audit-Server)
    "172.31.20.28",     # La IP Privada de este servidor (Audit-Server)
    "3.91.97.197",      # La IP Pública de Reportes
    "172.31.17.51",     # IP Privada Reportes 1
    "172.31.26.43",     # IP Privada Reportes 2
    "172.31.18.237",    # IP Privada Reportes 3
    "172.31.17.54",     # IP Privada Reportes 4
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "manejador_logs", 
    "logs",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "manejador_logs.urls"

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

# --- CONFIGURACIÓN DE LOGS PARA AWS CLOUDWATCH ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'cloudwatch': {
            'level': 'INFO',
            'class': 'watchtower.CloudWatchLogHandler',
            'boto3_client': boto3.client('logs', region_name='us-east-1'),
            'log_group': 'BITECO-Audit-Logs',
            'stream_name': 'audit-server-stream',
            'create_log_group': True,
            'send_interval': 1,       # Envío casi instantáneo
            'max_batch_count': 1,     # No esperar a acumular logs
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'cloudwatch'],
            'level': 'INFO',
            'propagate': True,
        },
        'manejador_logs': {  # Asegúrate que este nombre coincida con tu app
            'handlers': ['console', 'cloudwatch'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
