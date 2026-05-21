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