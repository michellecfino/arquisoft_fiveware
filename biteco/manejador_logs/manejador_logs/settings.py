from pathlib import Path
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "audit-secret-key-123")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "98.93.104.66",     # IP Pública Audit-Server
    "172.31.20.28",     # IP Privada Audit-Server
    "3.91.97.197",      # IP Pública Reportes
    "172.31.17.51", "172.31.26.43", "172.31.18.237", "172.31.17.54", # Privadas Reportes
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions", # <--- Asegúrate de tener esta
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "manejador_logs", 
    "logs",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "manejador_logs.urls"

# --- BLOQUE DE TEMPLATES (EL QUE NOS FALTABA) ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': { 'class': 'logging.StreamHandler' },
        'cloudwatch': {
            'level': 'INFO',
            'class': 'watchtower.CloudWatchLogHandler',
            'boto3_client': boto3.client('logs', region_name='us-east-1'),
            'log_group': 'BITECO-Audit-Logs',
            'stream_name': 'audit-server-stream',
            'create_log_group': True,
            'send_interval': 1,
            'max_batch_count': 1,
        },
    },
    'loggers': {
        'django': { 'handlers': ['console', 'cloudwatch'], 'level': 'INFO', 'propagate': True },
        'logs': { 'handlers': ['console', 'cloudwatch'], 'level': 'INFO', 'propagate': False },
    },
}

TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"