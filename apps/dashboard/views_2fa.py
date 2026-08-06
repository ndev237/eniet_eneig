"""
Vues de la double authentification (2FA TOTP) du dashboard.

Deux étapes distinctes :

  1. `setup`  — première configuration : génère un TOTPDevice non confirmé,
                affiche le QR code à scanner, demande le premier code, puis
                confirme le device (device.confirmed = True) et connecte
                l'utilisateur au niveau OTP dans sa session.

  2. `verify` — connexions suivantes : affiche uniquement la saisie du code
                à 6 chiffres, le valide contre le device confirmé, puis
                enregistre la vérification dans la session.

Le décorateur `otp_required_dashboard` (voir decorators.py) est le seul
point d'entrée qui garantit que ces deux vues sont bien parcourues au bon
moment — elles ne sont donc pas elles-mêmes décorées avec la 2FA
(cela créerait une boucle de redirection), seulement avec la protection
d'authentification classique.
"""

from base64 import b64encode
from io import BytesIO
from urllib.parse import urlparse

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice


# ============================================================
# Helpers
# ============================================================
def _qr_data_uri(payload: str) -> str:
    """
    Encode `payload` (l'URL otpauth://) en PNG puis en data URI base64.
    Pratique : l'image reste en mémoire, jamais écrite sur disque,
    donc pas d'exposition du secret sur le système de fichiers.
    """
    img = qrcode.make(payload, box_size=8, border=2)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + b64encode(buf.getvalue()).decode('ascii')


def _safe_next(request, default_name: str = 'dashboard:home') -> str:
    """
    Récupère un paramètre `next` du POST ou du GET, mais uniquement s'il
    pointe vers une URL relative (path only) sous /dashboard/. On refuse
    ainsi tout redirect externe (open redirect protection).
    """
    candidate = request.POST.get('next') or request.GET.get('next') or ''
    parsed = urlparse(candidate)
    # netloc vide + scheme vide = URL relative. On restreint au préfixe dashboard.
    if candidate and not parsed.netloc and not parsed.scheme and candidate.startswith('/'):
        return candidate
    return reverse(default_name)


# ============================================================
# 1. SETUP — première configuration
# ============================================================
@login_required(login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def setup_2fa(request):
    """
    Configuration initiale du 2FA pour l'utilisateur courant.

    Comportement :

      - Si l'utilisateur a déjà un device confirmé, on le renvoie sur le
        flux normal (verify si session non vérifiée, sinon home).
      - Sinon, on récupère (ou crée) un TOTPDevice non confirmé lié à lui,
        on affiche le QR code correspondant à `device.config_url`.
      - POST avec un code valide : `device.confirmed = True`, on connecte
        l'utilisateur au niveau OTP (django_otp.login) et on redirige.
    """
    user = request.user

    # Court-circuit : device déjà confirmé → on ne recrée pas.
    if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
        if request.user.is_verified():
            return redirect('dashboard:home')
        return redirect('dashboard:2fa_verify')

    # Un seul device non confirmé actif à la fois par utilisateur.
    device, created = TOTPDevice.objects.get_or_create(
        user=user, confirmed=False, defaults={'name': 'default'}
    )

    error = None
    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        if device.verify_token(code):
            # Confirmation : ce device est désormais celui utilisé pour vérifier.
            device.confirmed = True
            device.save()
            # otp_login pose le marqueur dans la session : is_verified() → True.
            otp_login(request, device)
            messages.success(
                request,
                "Double authentification activée avec succès."
            )
            return redirect('dashboard:home')
        error = "Le code saisi est invalide. Vérifiez que l'heure de votre "\
                "téléphone est à la bonne heure, puis réessayez."

    context = {
        'qr_data_uri': _qr_data_uri(device.config_url),
        # `device.config_url` a la forme otpauth://totp/Issuer:label?secret=...&issuer=...
        # On extrait la clé brute pour la saisie manuelle si le QR ne se scanne pas.
        'secret_key': device.bin_key.hex().upper(),
        'error': error,
    }
    return render(request, 'dashboard/auth/2fa_setup.html', context)


# ============================================================
# 2. VERIFY — connexions suivantes
# ============================================================
@login_required(login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def verify_2fa(request):
    """
    Saisie du code TOTP à chaque nouvelle session.

    - Si l'utilisateur n'a pas de device confirmé, on l'envoie au setup.
    - Si la session est déjà vérifiée, on l'envoie directement à la cible.
    - POST avec code valide → otp_login + redirection vers `next` (safe).
    """
    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if device is None:
        return redirect('dashboard:2fa_setup')

    if request.user.is_verified():
        return HttpResponseRedirect(_safe_next(request))

    error = None
    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        if device.verify_token(code):
            otp_login(request, device)
            return HttpResponseRedirect(_safe_next(request))
        error = "Code incorrect. Vérifiez le code affiché par votre application "\
                "authenticator et réessayez."

    context = {
        'next': _safe_next(request),
        'error': error,
    }
    return render(request, 'dashboard/auth/2fa_verify.html', context)


# ============================================================
# 3. HEARTBEAT — prolonge la session côté serveur
# ============================================================
@login_required(login_url='dashboard:login')
@require_POST
def session_heartbeat(request):
    """
    Endpoint sans effet visible autre que : le SessionMiddleware +
    SESSION_SAVE_EVERY_REQUEST=True s'occupent de réécrire la session
    avec un nouveau Max-Age → la fenêtre glissante de 10 minutes repart.

    Appelé par le JS quand l'utilisateur clique « Rester connecté »
    dans l'avertissement d'expiration. Retour 204 No Content = tout va bien.
    """
    return HttpResponse(status=204)
