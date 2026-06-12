"""
Django settings for ENIET/ENIEG project.
Documentation: https://docs.djangoproject.com/en/6.0/

Stratégie : 12-factor — tous les secrets et bascules d'environnement
sont lus dans des variables d'environnement (via un fichier .env en local).
Aucun secret ne doit être committé dans ce fichier.
"""

from pathlib import Path
import os

# ============================================================
# 1. CHEMINS DE BASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Chargement du .env (uniquement si python-dotenv est installé — silencieux sinon)
# Le .env n'existe qu'en local ; en prod les variables viennent de la plateforme.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


# ============================================================
# 2. HELPERS DE LECTURE D'ENVIRONNEMENT
# ============================================================
def env(key, default=None):
    """Récupère une variable d'env, retourne default si absente."""
    return os.environ.get(key, default)


def env_bool(key, default=False):
    """Lit un booléen depuis l'env : true/yes/on/1 → True, autre → False."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=''):
    """Lit une liste depuis l'env (séparateur virgule), nettoyée."""
    raw = os.environ.get(key, default)
    return [x.strip() for x in raw.split(',') if x.strip()]


# ============================================================
# 3. SÉCURITÉ
# ============================================================
# SECRET_KEY : obligatoire en prod, jamais committée.
# En dev (DEBUG=True), on tolère une clé de repli pour démarrer sans .env.
SECRET_KEY = env('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    # Repli DEV uniquement — bloque en prod (cf. ci-dessous).
    SECRET_KEY = 'django-insecure-DEV-ONLY-CHANGE-ME-IN-PROD'

# DEBUG = False par défaut → fail-safe : la prod marche même si la var oubliée.
DEBUG = env_bool('DJANGO_DEBUG', default=False)

# Hôtes autorisés. En dev par défaut ; en prod la plateforme doit fournir.
ALLOWED_HOSTS = env_list(
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1' if DEBUG else ''
)

# Garde-fou : refus de démarrer en prod avec la clé de repli.
if not DEBUG and SECRET_KEY.startswith('django-insecure-'):
    raise RuntimeError(
        "DJANGO_SECRET_KEY manquante en production. "
        "Définis-la dans l'environnement avant de démarrer."
    )

# CSRF : domaines de confiance (scheme://host obligatoire).
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')


# ============================================================
# 4. APPLICATIONS INSTALLÉES
# ============================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'tailwind',
    'theme',
    'tinymce',
]

LOCAL_APPS = [
    'apps.core',
    'apps.pages',
    'apps.ecoles',
    'apps.blog',
    'apps.contacts',
    'apps.dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ============================================================
# 5. MIDDLEWARE
# ============================================================
# WhiteNoise sert les fichiers statiques compressés en prod, juste derrière
# SecurityMiddleware. Si la lib n'est pas installée (ex: en dev), on saute.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

try:
    import whitenoise  # noqa: F401
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
except ImportError:
    pass

MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'


# ============================================================
# 6. TEMPLATES
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.dashboard_badges',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ============================================================
# 7. BASE DE DONNÉES — SQLite en dev, PostgreSQL en prod
# ============================================================
# Bascule via DJANGO_DB_ENGINE : 'sqlite' (défaut) ou 'postgres'.
# En prod sur PostgreSQL : on attend les 5 variables DJANGO_DB_*.
DB_ENGINE = env('DJANGO_DB_ENGINE', 'sqlite').lower()

if DB_ENGINE in ('postgres', 'postgresql', 'pg'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DJANGO_DB_NAME', 'eniet_eneig'),
            'USER': env('DJANGO_DB_USER', 'eniet_eneig'),
            'PASSWORD': env('DJANGO_DB_PASSWORD', ''),
            'HOST': env('DJANGO_DB_HOST', 'localhost'),
            'PORT': env('DJANGO_DB_PORT', '5432'),
            # Connexions persistantes — réduit la latence et la charge BDD.
            'CONN_MAX_AGE': int(env('DJANGO_DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                # SSL recommandé en prod ; désactivable via env si la BDD locale.
                'sslmode': env('DJANGO_DB_SSLMODE', 'prefer'),
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ============================================================
# 8. VALIDATION DES MOTS DE PASSE
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================================
# 9. INTERNATIONALISATION
# ============================================================
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'fr'

LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True


# ============================================================
# 10. FICHIERS STATIQUES
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise : versionne et compresse les statiques (long-cache safe).
# Si whitenoise n'est pas installé, Django utilise le stockage standard.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE and not DEBUG
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}


# ============================================================
# 11. FICHIERS MÉDIAS (uploads)
# ============================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# 12. DJANGO-TAILWIND
# ============================================================
TAILWIND_APP_NAME = 'theme'

NPM_BIN_PATH = env('NPM_BIN_PATH', r'C:\Program Files\nodejs\npm.cmd')
INTERNAL_IPS = ['127.0.0.1']


# ============================================================
# 13. DIVERS
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# 14. EMAIL
# ============================================================
EMAIL_BACKEND = env(
    'DJANGO_EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = env('DJANGO_EMAIL_HOST', '')
EMAIL_PORT = int(env('DJANGO_EMAIL_PORT', '587'))
EMAIL_HOST_USER = env('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('DJANGO_EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env_bool('DJANGO_EMAIL_USE_SSL', default=False)
DEFAULT_FROM_EMAIL = env('DJANGO_DEFAULT_FROM_EMAIL', 'noreply@eniet-eneig.cm')
CONTACT_EMAIL = env('DJANGO_CONTACT_EMAIL', 'efpsaf@yahoo.fr')


# ============================================================
# 15. AUTHENTIFICATION ET DASHBOARD
# ============================================================
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGIN_URL = 'dashboard:login'
LOGOUT_REDIRECT_URL = 'dashboard:login'


# ============================================================
# 16. TINYMCE
# ============================================================
TINYMCE_DEFAULT_CONFIG = {
    'api_key': env('TINYMCE_API_KEY', 'zrehrwjgfxgqjzkfknb0e75jbye4hlvkzitgil0sdo8ci145'),
    'height': 500,
    'menubar': False,
    'plugins': (
        'advlist autolink lists link image charmap print preview anchor '
        'searchreplace visualblocks code fullscreen '
        'insertdatetime media table paste code help wordcount'
    ),
    'toolbar': (
        'undo redo | formatselect | bold italic underline | '
        'alignleft aligncenter alignright alignjustify | '
        'bullist numlist outdent indent | link image | removeformat | code | help'
    ),
    'block_formats': (
        'Paragraphe=p; Titre H2=h2; Titre H3=h3; Citation=blockquote'
    ),
    'content_style': (
        'body { font-family: Inter, sans-serif; font-size: 16px; line-height: 1.7; }'
    ),
    'language': 'fr_FR',
    'branding': False,
    'promotion': False,
    'images_upload_url': '/dashboard/tinymce/upload-image/',
}


# ============================================================
# 17. SÉCURITÉ DE PRODUCTION
# ============================================================
# Tous ces réglages ne s'appliquent que lorsque DEBUG=False.
# Le proxy header est nécessaire derrière nginx/Cloudflare qui terminent le TLS.
if not DEBUG:
    # Cookies : transmis uniquement sur HTTPS, non lisibles par JS.
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'

    # Force la redirection HTTP → HTTPS (à désactiver si la plateforme la gère).
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', default=True)

    # HSTS : le navigateur exige HTTPS pendant N secondes (1 an par défaut).
    SECURE_HSTS_SECONDS = int(env('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
    SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', default=False)

    # Anti-sniffing + politique referrer raisonnable.
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

    # Behind a TLS-terminating proxy (nginx, Cloudflare, Heroku, etc.) :
    # Django doit savoir que la requête entrante est sécurisée.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Anti-clickjacking strict.
    X_FRAME_OPTIONS = 'DENY'


# ============================================================
# 18. LOGGING — utile en prod pour tracer les erreurs sans DEBUG
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
