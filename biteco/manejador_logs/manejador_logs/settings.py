from pathlib import Path
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "audit-secret-key-123")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["54.83.17.153","52.54.68.52", "10.0.2.215","34.201.42.208",
  "10.0.2.139",
  "10.0.2.123",
  "10.0.2.67",
  "10.0.2.156",
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
        "PASSWORD": os.getenv("DB_PASSWORD", "biteco12345"),
        "HOST": os.getenv("DB_HOST", "audit-db.c4mxolen2vp8.us-east-1.rds.amazonaws.com"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"