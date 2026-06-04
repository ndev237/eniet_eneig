"""
Décorateurs personnalisés pour le contrôle d'accès du dashboard.
"""

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def super_admin_required(view_func):
    """
    Décorateur qui restreint l'accès aux super-administrateurs.

    Comment ça marche ?
    - @wraps préserve le nom et la doc de la fonction décorée
    - On vérifie que l'utilisateur est connecté ET super_admin
    - Sinon : message d'erreur + redirection vers l'accueil dashboard

    Utilisation :
        @login_required(login_url='dashboard:login')
        @super_admin_required
        def ma_vue(request):
            ...

    IMPORTANT : @super_admin_required doit venir APRÈS @login_required
    car on a besoin que l'utilisateur soit déjà authentifié pour
    vérifier son rôle.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # L'utilisateur doit avoir un profil et être super_admin
        # hasattr vérifie que le profil existe (sécurité)
        if not hasattr(request.user, 'profil') or not request.user.profil.est_super_admin:
            messages.error(
                request,
                "Accès refusé. Cette section est réservée aux administrateurs."
            )
            return redirect('dashboard:home')

        # Tout est OK, on exécute la vue normale
        return view_func(request, *args, **kwargs)

    return wrapper