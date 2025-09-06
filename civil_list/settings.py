from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY","django-insecure-change-me")
DEBUG = True
ALLOWED_HOSTS = ["*"]


AUTHENTICATION_BACKENDS = [                        # <— add this first
    "django.contrib.auth.backends.ModelBackend",
]

INSTALLED_APPS = [
    "jazzmin",                    # <-- add this FIRST (before 'django.contrib.admin')
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    "hr",
]
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/hr/portal/"
LOGOUT_REDIRECT_URL = "/accounts/login/"     # or "/accounts/login/"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR/'media'


JAZZMIN_SETTINGS = {
    "site_url": "/admin/", 
    "site_title": "DSTTE SEVA ITIHAS PORTAL",     # Browser tab title
    "site_header": "DSTTE SEVA ITIHAS PORTAL",    # Top-left header text
    "site_brand": "DSTTE SEVA ITIHAS",            # Small brand next to logo
    "welcome_sign": "Welcome to DSTTE SEVA ITIHAS PORTAL",
    "copyright": "DSTTE",

    # Features
    "show_ui_builder": False,

    # Top menu shortcut to the HR portal

    # Theme & styling
    "theme": "cosmo",          # Bootstrap base theme
    "dark_mode_theme": "slate",
    "brand_colour": "#800000", # Maroon as brand
    "accent": "brand",

    # Custom assets (only once!)
    "custom_css": "css/custom.css",   # override colors/fonts
    "custom_js": "js/admin_tailwind_theme.js",
        # inject Tailwind or tweaks
}

JAZZMIN_UI_TWEAKS = {
    "show_ui_builder": False,   # (you already have this probably)
    "footer_show_version": False,  # hides Django/Jazzmin version
}
USE_I18N = True
LANGUAGE_CODE = "en-us"

LANGUAGES = [
    ("en", "English"),
    ("hi", "हिन्दी"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]



MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "hr.middleware.AdminSuperuserOnlyMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "hr.middleware.ForcePasswordChangeMiddleware",  # <== add here
]
LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_SAMESITE = "Lax"
LANGUAGE_COOKIE_SECURE = False      # set True only if your site is HTTPS-only
LANGUAGE_COOKIE_PATH = "/"

ROOT_URLCONF = "civil_list.urls"
TEMPLATES = [{
    "BACKEND":"django.template.backends.django.DjangoTemplates",
    "DIRS":[BASE_DIR/"templates"], "APP_DIRS":True,
    "OPTIONS":{"context_processors":[
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.template.context_processors.i18n",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "hr.context_processors.dashboard_url", 
    ]},
}]
WSGI_APPLICATION = "civil_list.wsgi.application"
DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.mysql",
    "NAME": "civil_hrms6",
    "USER": "root",
    "PASSWORD": "umarf123@",
    "HOST": "127.0.0.1",
    "PORT": "3306",
    "OPTIONS": {"charset":"utf8mb4","init_command":"SET sql_mode='STRICT_TRANS_TABLES'"},
  }
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
LANGUAGE_CODE="en-us"; TIME_ZONE="Asia/Kolkata"; USE_I18N=True; USE_TZ=True
STATIC_URL="static/"; STATIC_ROOT=BASE_DIR/"staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"



