"""
Context processors globaux du projet.

Un context processor est une fonction qui prend une requête et retourne
un dictionnaire. Les clés de ce dictionnaire deviennent automatiquement
des variables accessibles dans TOUS les templates.

Sans context processor :
    Chaque vue doit faire :
    return render(request, 'template.html', {
        'site_settings': SiteSettings.load(),
        ...
    })

Avec context processor :
    {{ site_settings.email_principal }} fonctionne partout
    sans avoir à le passer depuis chaque vue.
"""

from apps.pages.models import SiteSettings
from apps.contacts.models import MessageContact
from django.conf import settings

def tinymce_key(request):
    return {
        'TINYMCE_API_KEY': getattr(settings, 'TINYMCE_API_KEY', '')
    }

def site_settings(request):
    """
    Injecte les paramètres du site dans tous les templates.

    Utilisation dans les templates :
        {{ site_settings.email_principal }}
        {{ site_settings.telephone_1 }}
        {{ site_settings.adresse_ligne_1 }}
    """
    return {
        'site_settings': SiteSettings.load(),
    }


def dashboard_badges(request):
    """
    Compteurs pour les badges de la sidebar du dashboard.

    On ne charge ces compteurs que si l'utilisateur est connecté
    pour éviter des requêtes inutiles sur le site public.
    """
    # Pas de badges si pas connecté ou pas dans le dashboard
    if not request.user.is_authenticated:
        return {}

    # On évite la requête sur les pages publiques (optimisation)
    if not request.path.startswith('/dashboard'):
        return {}

    nb_messages_non_lus = MessageContact.objects.filter(
        statut=MessageContact.StatutChoices.NON_LU
    ).count()

    return {
        'badge_messages_non_lus': nb_messages_non_lus,
    }

