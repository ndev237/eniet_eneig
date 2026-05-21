from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class MessageContact(TimeStampedModel):
    """
    Représente un message envoyé via le formulaire de contact du site.

    Hérite de TimeStampedModel → obtient created_at et updated_at gratuitement.
    """

    # ============================================================
    # Choix pour le sujet du message (liste déroulante côté front)
    # On utilise des constantes pour éviter les chaînes "magiques"
    # ============================================================
    class SujetChoices(models.TextChoices):
        """
        TextChoices est une classe Django moderne (depuis 3.0) qui
        remplace les anciens 'choices' à base de tuples.

        Chaque choix a 3 parties :
        - Nom de la constante (NOM_DU_CHOIX)
        - Valeur stockée en BDD ('valeur_courte')
        - Libellé affiché ('Texte traduisible')
        """
        INFO_GENERALE = 'info', _('Demande d\'information')
        ADMISSION = 'admission', _('Question sur l\'admission')
        FORMATION = 'formation', _('Question sur les formations')
        PARTENARIAT = 'partenariat', _('Proposition de partenariat')
        AUTRE = 'autre', _('Autre')

    # ============================================================
    # Statut du message - workflow simple pour le dashboard
    # ============================================================
    class StatutChoices(models.TextChoices):
        NON_LU = 'non_lu', _('Non lu')
        LU = 'lu', _('Lu')
        TRAITE = 'traite', _('Traité')

    # ============================================================
    # CHAMPS DU MODÈLE
    # ============================================================

    # Identité de l'expéditeur
    nom = models.CharField(
        _('Nom complet'),
        max_length=150,
        help_text=_('Nom et prénom de la personne'),
    )

    email = models.EmailField(
        _('Adresse email'),
        # EmailField valide automatiquement le format email@domaine.tld
        # Pas besoin de regex à la main
    )

    telephone = models.CharField(
        _('Téléphone'),
        max_length=30,
        blank=True,  # ← optionnel, peut être vide
        help_text=_('Numéro de téléphone (optionnel)'),
    )

    # Métadonnées du message
    sujet = models.CharField(
        _('Sujet'),
        max_length=20,
        choices=SujetChoices.choices,
        default=SujetChoices.INFO_GENERALE,
    )

    message = models.TextField(
        _('Message'),
        help_text=_('Contenu du message'),
    )

    # Statut administratif - manipulé par l'admin via le dashboard
    statut = models.CharField(
        _('Statut'),
        max_length=10,
        choices=StatutChoices.choices,
        default=StatutChoices.NON_LU,
    )

    # Note interne de l'admin (pas visible par l'expéditeur)
    note_interne = models.TextField(
        _('Note interne'),
        blank=True,
        help_text=_('Notes privées de l\'équipe (non visible par l\'expéditeur)'),
    )

    class Meta:
        verbose_name = _('Message de contact')
        verbose_name_plural = _('Messages de contact')
        # ordering : par défaut, on affiche les messages du plus récent au plus ancien
        # Le '-' devant created_at signifie 'ordre décroissant'
        ordering = ['-created_at']

    def __str__(self):
        """
        Représentation textuelle d'un message.
        Utilisée dans l'admin Django et partout où on print(message).
        """
        return f"{self.nom} — {self.get_sujet_display()} ({self.created_at:%d/%m/%Y})"

    @property
    def est_non_lu(self):
        """
        Propriété qui retourne True si le message n'a pas été lu.
        Permet d'écrire dans les templates : {% if message.est_non_lu %}
        au lieu de : {% if message.statut == 'non_lu' %}
        """
        return self.statut == self.StatutChoices.NON_LU