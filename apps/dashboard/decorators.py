"""
Décorateurs personnalisés pour le contrôle d'accès du dashboard.
"""

from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


# ============================================================
# 2FA — Décorateur unique de porte d'entrée du dashboard
# ============================================================
def otp_required_dashboard(view_func):
    """
    Décorateur combiné qui REMPLACE @login_required sur le dashboard.

    Il applique la chaîne de sécurité complète :

        1. non connecté             → redirige vers dashboard:login
        2. connecté, pas de device
           TOTP confirmé            → redirige vers dashboard:2fa_setup
        3. connecté avec device
           mais not is_verified()   → redirige vers dashboard:2fa_verify
                                      (avec ?next= pour reprendre où l'utilisateur
                                       voulait aller)
        4. connecté + vérifié       → exécute la vue

    request.user.is_verified() vient du OTPMiddleware. Il vaut True dès qu'un
    device a été confirmé dans la session courante via django_otp.login().
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 1. Auth de base — équivaut à @login_required.
        if not request.user.is_authenticated:
            return redirect(
                f"{reverse('dashboard:login')}?{urlencode({'next': request.get_full_path()})}"
            )

        # Import local pour éviter d'importer les modèles django_otp au chargement
        # du module (Django n'est pas encore complètement configuré à l'import).
        from django_otp.plugins.otp_totp.models import TOTPDevice

        # 2. Existence d'un device TOTP confirmé.
        has_confirmed_device = TOTPDevice.objects.filter(
            user=request.user, confirmed=True
        ).exists()

        if not has_confirmed_device:
            # Premier accès (ou device supprimé par un admin) → configuration obligatoire.
            return redirect('dashboard:2fa_setup')

        # 3. Device présent mais code non validé pour cette session.
        if not request.user.is_verified():
            next_url = request.get_full_path()
            return redirect(
                f"{reverse('dashboard:2fa_verify')}?{urlencode({'next': next_url})}"
            )

        # 4. Tout OK.
        return view_func(request, *args, **kwargs)

    return wrapper


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