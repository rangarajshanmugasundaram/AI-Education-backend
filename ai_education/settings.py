from pathlib import Path
from datetime import timedelta
import os
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-73xhfnh+(61itd5918pn5%ivof2r2@$jvt-*$**^u)=05*qp01')

DEBUG = True

ALLOWED_HOSTS = ['*']

RECONNECT_TIMEOUT_SECONDS = 120

INSTALLED_APPS = [
    'daphne',
    'channels',

    # Third Party Apps
    'rest_framework',
    'corsheaders',

    # Modular Local Apps
    'authentication.apps.AuthenticationConfig',
    'attendance.apps.AttendanceConfig',
    'chat.apps.ChatConfig',
    'whiteboard.apps.WhiteboardConfig',
    'classroom.apps.ClassroomConfig',
    'notifications.apps.NotificationsConfig',
    'feedback',
    'recordings.apps.RecordingsConfig',
    'admin_dashboard.apps.AdminDashboardConfig',
    'user_management.apps.UserManagementConfig',
    'course_management.apps.CourseManagementConfig',
    'batch_management.apps.BatchManagementConfig',
    'exams',

    # Core Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must stay on top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

ROOT_URLCONF = 'ai_education.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_education.wsgi.application'
ASGI_APPLICATION = 'ai_education.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'rangarajshanmugasundaram@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# --- GLOBAL CORS CONFIGURATION ---
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# 🌟 ADDED: Custom User Headers allowed in CORS preflight checks
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-user-email',
    'x-user-role',
    'x-user-id',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
APPEND_SLASH = True