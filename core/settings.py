import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-l0vixtoy9p^t#(3871o%1peqs3imc4x3hfk_c90=s)%f*&7%-('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    'budget.apps.BudgetConfig',  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Menambahkan BASE_DIR / 'templates' agar folder template global terbaca
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'budget.context_processors.global_context',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database MySQL
# Pastikan XAMPP/MySQL kamu sudah jalan dan database 'makan_mana' sudah dibuat
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'makan_mana',    
        'USER': 'root',          
        'PASSWORD': '',      
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization (Pengaturan Bahasa Indonesia)
LANGUAGE_CODE = 'id'  # Mengubah ke Bahasa Indonesia
TIME_ZONE = 'Asia/Makassar' # Sesuaikan dengan waktu WITA (Samarinda)
USE_I18N = True
USE_TZ = False
USE_L10N = True
USE_THOUSAND_SEPARATOR = True # Agar angka muncul titik (misal: 10.000)

# Static & Media Files
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# AUTHENTICATION REDIRECTS (PENTING)
# ==========================================
# URL Login (jika user mencoba akses dashboard tanpa login)
LOGIN_URL = '/accounts/login/'

# Ke mana user pergi setelah berhasil login
LOGIN_REDIRECT_URL = '/redirect/'

# Ke mana user pergi setelah logout
LOGOUT_REDIRECT_URL = '/accounts/login/'