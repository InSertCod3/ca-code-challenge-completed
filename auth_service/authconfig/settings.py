import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "LOCAL-DEVELOPMENT-ONLY") + "-auth"
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.getenv("AUTH_ALLOWED_HOSTS", "localhost,127.0.0.1,auth").split(",")
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "identities"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "authconfig.urls"
TEMPLATES = []
WSGI_APPLICATION = "authconfig.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME", "identities"),
        "USER": os.getenv("DB_USER", "identities"),
        "PASSWORD": os.getenv("DB_PASSWORD", "identities"),
        "HOST": os.getenv("DB_HOST", "auth_db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
AUTH_USER_MODEL = "identities.User"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
