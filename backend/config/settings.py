from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-bcrm-default-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    # Local apps
    'apps.users',
    'apps.products',
    'apps.customers',
    'apps.sales',
    'apps.purchases',
    'apps.reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
if os.getenv('DB_ENGINE'):
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Swagger / OpenAPI
SPECTACULAR_SETTINGS = {
    'TITLE': 'BalonCRM API',
    'DESCRIPTION': (
        'BalonCRM - balon va bezak do\'koni uchun CRM tizimi REST API.\n\n'
        '## Autentifikatsiya\n'
        'Barcha endpointlar (login bundan mustasno) JWT Bearer token talab qiladi.\n\n'
        '**Token olish:** `POST /api/auth/login/` → `access` tokenini oling.\n\n'
        '**So\'rovda ishlatish:** `Authorization: Bearer <access_token>`\n\n'
        '## Asosiy tushunchalar\n'
        '- **Mahsulot** — `cost_price` (tan narx) va `sale_price` (sotuv narxi) ikki alohida narx\n'
        '- **Sotuv** — har bir bandda `price` frontentdan keladi (o\'zgartirish mumkin)\n'
        '- **Harid** — mahsulotni omborga kiritadi, `cost_price` ni yangilaydi\n'
        '- **Sof foyda** = Sotuv jami − (tan narx × miqdor)\n'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'auth', 'description': 'Login, logout, token yangilash'},
        {'name': 'products', 'description': 'Mahsulotlar va kategoriyalar'},
        {'name': 'customers', 'description': 'Mijozlar boshqaruvi'},
        {'name': 'sales', 'description': 'Sotuvlar'},
        {'name': 'purchases', 'description': 'Haridlar (omborga kirim)'},
        {'name': 'reports', 'description': 'Hisobotlar va statistika'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'filter': True,
    },
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '')
TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')

JAZZMIN_SETTINGS = {
    'site_title': 'BalonCRM Admin',
    'site_header': 'BalonCRM',
    'site_brand': 'BalonCRM',
    'welcome_sign': 'BalonCRM boshqaruv paneli',
    'copyright': 'BalonCRM',
    'search_model': ['users.User', 'users.TelegramBotUser', 'products.Product', 'customers.Customer'],
    'topmenu_links': [
        {'name': 'Bosh sahifa', 'url': 'admin:index', 'permissions': ['users.view_user']},
        {'model': 'users.User'},
        {'model': 'users.TelegramBotUser'},
    ],
    'usermenu_links': [
        {'model': 'users.User'},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'order_with_respect_to': [
        'users',
        'products',
        'customers',
        'sales',
        'purchases',
        'reports',
    ],
    'icons': {
        'users.User': 'fas fa-users',
        'users.TelegramBotUser': 'fab fa-telegram-plane',
        'products.Product': 'fas fa-box',
        'products.Category': 'fas fa-tags',
        'customers.Customer': 'fas fa-address-book',
        'sales.Sale': 'fas fa-cash-register',
        'purchases.Purchase': 'fas fa-truck-loading',
    },
}

JAZZMIN_UI_TWEAKS = {
    'theme': 'flatly',
    'navbar': 'navbar-white navbar-light',
    'sidebar': 'sidebar-dark-primary',
    'brand_colour': 'navbar-primary',
    'accent': 'accent-primary',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-outline-secondary',
        'success': 'btn-success',
        'danger': 'btn-danger',
        'warning': 'btn-warning',
        'info': 'btn-info',
    },
}
