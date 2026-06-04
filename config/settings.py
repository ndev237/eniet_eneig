"""
Django settings for ENIET/ENIEG project.
Documentation: https://docs.djangoproject.com/en/6.0/
"""

from pathlib import Path
import os

# ============================================================
# 1. CHEMINS DE BASE
# ============================================================
# BASE_DIR pointe vers le dossier racine du projet (celui qui contient manage.py)
# On utilise pathlib.Path pour avoir une gestion multi-OS (Windows/Linux)
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 2. SÉCURITÉ
# ============================================================
# ⚠️ Cette clé doit être secrète en production - on la sortira dans .env plus tard
SECRET_KEY = 'django-insecure-u(4+vh*ewfj-%-*#!4g9w@eu3sl2ngiip^)^o7^o3vf%7ii8#v'

# DEBUG=True en dev seulement. Affiche les erreurs détaillées dans le navigateur.
# En production : DEBUG=False obligatoirement pour des raisons de sécurité.
DEBUG = True

# Liste des domaines autorisés à servir le site
# En dev : localhost. En prod : on ajoutera 'eniet-eneig.cm' etc.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# ============================================================
# 3. APPLICATIONS INSTALLÉES
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

# Apps tierces (installées via pip)
THIRD_PARTY_APPS = [
    'tailwind',
    'theme',
    'tinymce',
]

# Nos propres apps - on les ajoutera au fur et à mesure
LOCAL_APPS = [
    'apps.core',
    'apps.pages',
    'apps.ecoles',
    'apps.blog',
    # 'apps.medias',
    'apps.contacts',
    # 'apps.accounts',
    'apps.dashboard',
]

# Concaténation des 3 listes - pattern pro pour rester organisé quand le projet grandit
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ============================================================
# 4. MIDDLEWARE (l'ORDRE EST CRITIQUE !)
# ============================================================
# Le middleware traite chaque requête HTTP de haut en bas (entrée),
# et chaque réponse de bas en haut (sortie).
# LocaleMiddleware DOIT être placé APRÈS SessionMiddleware (besoin de la session)
# et AVANT CommonMiddleware (qui fait des redirections).
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ← Ajouté pour le bilingue
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'


# ============================================================
# 5. TEMPLATES
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DIRS = liste des dossiers où Django cherche les templates en priorité
        # On ajoute le dossier 'templates/' à la racine pour nos templates globaux
        'DIRS': [BASE_DIR / 'templates'],
        # APP_DIRS=True : Django cherche aussi dans chaque app/templates/
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',  # ← Pour LANGUAGE_CODE dans les templates
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
# 6. BASE DE DONNÉES
# ============================================================
# En dev : SQLite (simple, fichier unique)
# En prod : on basculera sur PostgreSQL via une variable d'environnement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ============================================================
# 7. VALIDATION DES MOTS DE PASSE
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================================
# 8. INTERNATIONALISATION (i18n) - SITE BILINGUE FR/EN
# ============================================================
from django.utils.translation import gettext_lazy as _

# Langue par défaut quand le navigateur ne précise rien
LANGUAGE_CODE = 'fr'

# Langues supportées par le site
# Le tuple (code, nom traduisible) sera utilisé par le sélecteur de langue
LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
]

# Dossier où Django va stocker/chercher les fichiers de traduction (.po et .mo)
# On le créera à la prochaine étape
LOCALE_PATHS = [BASE_DIR / 'locale']

# Fuseau horaire pour le Cameroun (Africa/Douala = UTC+1, pas de changement d'heure)
TIME_ZONE = 'Africa/Douala'

# Active le système d'internationalisation Django
USE_I18N = True

# Stocke les dates en UTC en base, convertit à l'affichage selon TIME_ZONE
USE_TZ = True


# ============================================================
# 9. FICHIERS STATIQUES (CSS, JS, images du design)
# ============================================================
# URL de base pour accéder aux fichiers statiques dans le navigateur
STATIC_URL = '/static/'

# Dossiers où Django va chercher les fichiers statiques en mode dev
# (en plus de chaque app/static/)
STATICFILES_DIRS = [BASE_DIR / 'static']

# Dossier où collectstatic regroupera tous les statiques pour la prod
# (Django collectera tous les /static/ des apps ici lors du déploiement)
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# 10. FICHIERS MÉDIAS (uploads des utilisateurs : photos d'articles, etc.)
# ============================================================
# Important : MEDIA est différent de STATIC.
# STATIC = fichiers du développeur (CSS, JS, logo)
# MEDIA = fichiers uploadés par les utilisateurs (photos d'articles, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# 11. DJANGO-TAILWIND
# ============================================================
TAILWIND_APP_NAME = 'theme'

# Chemin vers npm sur Windows - à adapter si chemin différent chez toi
NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'

# IPs internes - pour le hot-reload de Tailwind en dev
INTERNAL_IPS = ['127.0.0.1']


# ============================================================
# 12. DIVERS
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# ============================================================
# 13. EMAIL
# ============================================================
# En développement : on affiche les emails dans la console au lieu de les envoyer
# Permet de tester sans configurer SMTP, et sans spammer une vraie boîte mail
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Email d'expédition par défaut
DEFAULT_FROM_EMAIL = 'noreply@eniet-eneig.cm'

# Email destinataire pour les notifications du site
CONTACT_EMAIL = 'efpsaf@yahoo.fr'

# Plus tard en production, on remplacera EMAIL_BACKEND par SMTP :
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.hostinger.com'
# EMAIL_HOST_USER = '...'
# EMAIL_HOST_PASSWORD = '...' (en variable d'environnement)
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True

# ============================================================
# 14. AUTHENTIFICATION ET DASHBOARD
# ============================================================
# URL de redirection après connexion réussie
LOGIN_REDIRECT_URL = 'dashboard:home'

# URL de redirection si une page nécessite une connexion
LOGIN_URL = 'dashboard:login'

# URL après déconnexion
LOGOUT_REDIRECT_URL = 'dashboard:login'

# ============================================================
# 15. ÉDITEUR DE TEXTE ENRICHI (TinyMCE)
# ============================================================
TINYMCE_DEFAULT_CONFIG = {
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
    # Format select : niveaux de titres autorisés
    'block_formats': (
        'Paragraphe=p; Titre H2=h2; Titre H3=h3; Citation=blockquote'
    ),
    'content_style': (
        'body { font-family: Inter, sans-serif; font-size: 16px; line-height: 1.7; }'
    ),
    'language': 'fr_FR',
    'branding': False,  # Cache le logo TinyMCE
    'promotion': False,
    'images_upload_url': '/dashboard/tinymce/upload-image/',  # Pour uploader des images dans l'article
}