from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings

from .forms import ContactForm


def contact_view(request):
    """
    Vue de la page contact.

    Pattern Django classique : une seule vue gère GET (afficher le formulaire)
    et POST (traiter la soumission). C'est plus simple qu'avoir deux vues séparées.

    Workflow :
    1. GET → afficher le formulaire vide
    2. POST → valider les données
       - Si valide : sauvegarder + email + redirection + flash message
       - Si invalide : ré-afficher le formulaire avec les erreurs
    """

    if request.method == 'POST':
        # request.POST contient les données soumises
        # On les passe au formulaire pour validation
        form = ContactForm(request.POST)

        if form.is_valid():
            # form.save() crée et enregistre l'objet MessageContact
            # commit=False permettrait de modifier avant save, ici inutile
            message_obj = form.save()

            # ============================================================
            # ENVOI D'EMAIL DE NOTIFICATION À L'ADMIN
            # ============================================================
            try:
                envoyer_notification_admin(message_obj)
            except Exception as e:
                # Si l'email échoue, on continue quand même
                # Le message est sauvegardé en BDD, l'admin pourra le voir
                # Log l'erreur en console pour debug
                print(f"Erreur envoi email : {e}")

            # ============================================================
            # MESSAGE FLASH DE CONFIRMATION
            # ============================================================
            # Le système de messages Django stocke un message en session
            # qui sera affiché lors du prochain affichage de page
            messages.success(
                request,
                _('Votre message a bien été envoyé ! Nous vous répondrons dans les meilleurs délais.')
            )

            # ============================================================
            # REDIRECTION (pattern PRG : Post-Redirect-Get)
            # ============================================================
            # Pourquoi rediriger après POST ?
            # Pour éviter que l'utilisateur ré-soumette le formulaire
            # en rafraîchissant la page (F5).
            return redirect('contacts:contact')

        # Si form.is_valid() est False, on tombe ici
        # On affiche un message d'erreur générique
        messages.error(
            request,
            _('Veuillez corriger les erreurs ci-dessous.')
        )

    else:
        # Méthode GET : formulaire vide
        form = ContactForm()

    # Affichage du template avec le formulaire (vide ou avec erreurs)
    return render(request, 'contacts/contact.html', {
        'form': form,
    })


def envoyer_notification_admin(message_obj):
    """
    Envoie un email à l'admin du site quand un nouveau message arrive.

    Sépare la logique d'email de la vue pour respecter le SRP
    (Single Responsibility Principle).
    """
    sujet = f"[Site ENIET/ENIEG] Nouveau message : {message_obj.get_sujet_display()}"

    corps = f"""Nouveau message reçu via le formulaire de contact.

Expéditeur : {message_obj.nom}
Email : {message_obj.email}
Téléphone : {message_obj.telephone or 'Non renseigné'}
Sujet : {message_obj.get_sujet_display()}

Message :
{message_obj.message}

---
Reçu le {message_obj.created_at:%d/%m/%Y à %H:%M}
"""

    send_mail(
        subject=sujet,
        message=corps,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.CONTACT_EMAIL],
        fail_silently=False,  # Lève une exception si erreur (capturée par la vue)
    )