"""
Django settings for immo_congo project.
"""

import os
from pathlib import Path

# try:
#     import cloudinary  # noqa: F401
#     import cloudinary_storage  # noqa: F401
# except ImportError:  # pragma: no cover - tolerate build environments before deps settle
#     cloudinary = None
#     cloudinary_storage = None

try:
    import dj_database_url
except ImportError:  # pragma: no cover - local fallback before installing prod deps
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-mon^a%8f^e+goc(%fk-fqzot^)6ttwh@kb4h3ikpjlq^=5hz4o',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
USE_WHITENOISE = os.environ.get('USE_WHITENOISE', '1').lower() in {'1', 'true', 'yes'}


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'annonces',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'immo_congo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'annonces.context_processors.moderation_access',
            ],
        },
    },
]

WSGI_APPLICATION = 'immo_congo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if dj_database_url and os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False,
    )


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Africa/Kinshasa'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
WHITENOISE_USE_FINDERS = True

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        if USE_WHITENOISE
        else 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@immocongo.cd'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autoriser Railway pour la sécurité des formulaires (CSRF)
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-2ce12.up.railway.app',
]

# if cloudinary and cloudinary_storage:
#     INSTALLED_APPS.insert(0, 'cloudinary_storage')
#     INSTALLED_APPS.insert(1, 'cloudinary')

# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
#     'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
#     'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
# }

# DEFAULT_FILE_STORAGE = (
#     'cloudinary_storage.storage.MediaCloudinaryStorage'
#     if cloudinary and cloudinary_storage
#     else 'django.core.files.storage.FileSystemStorage'
# )
