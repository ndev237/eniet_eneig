from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import TimeStampedModel


class Profil(TimeStampedModel):
    """
    Profil étendu de l'utilisateur.

    Pourquoi un Profil séparé du User ?
    - User Django par défaut a : username, email, first_name, last_name, password
    - On veut ajouter : photo, rôle, biographie, téléphone
    - Solution : modèle Profil lié en OneToOne au User

    Pattern OneToOneField :
    - Une ligne dans Profil pour exactement une ligne dans User
    - Différent de ForeignKey (N-1) : c'est strictement 1-1
    - L'accès se fait via user.profil (et inversement profil.user)
    """

    class Role(models.TextChoices):
        """
        Rôles dans le dashboard.

        Différence entre les rôles :
        - SUPER_ADMIN : accès total (paramètres, utilisateurs, tout)
        - EDITEUR : peut publier des articles, voir messages
        - LECTEUR : consultation uniquement (statistiques, archives)
        """
        SUPER_ADMIN = 'super_admin', _('Super administrateur')
        EDITEUR = 'editeur', _('Éditeur')
        LECTEUR = 'lecteur', _('Lecteur')

    # ============================================================
    # LIEN VERS LE USER DJANGO
    # ============================================================
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # Si on supprime le User, on supprime le Profil
        related_name='profil',
        verbose_name=_('Utilisateur'),
    )

    # ============================================================
    # CHAMPS ADDITIONNELS
    # ============================================================
    role = models.CharField(
        _('Rôle'),
        max_length=20,
        choices=Role.choices,
        default=Role.EDITEUR,
    )

    photo = models.ImageField(
        _('Photo de profil'),
        upload_to='profils/',
        blank=True,
        null=True,
        help_text=_('Photo carrée recommandée'),
    )

    biographie = models.TextField(
        _('Biographie'),
        blank=True,
        help_text=_('Courte présentation, affichée sur les articles'),
    )

    telephone = models.CharField(
        _('Téléphone'),
        max_length=30,
        blank=True,
    )

    fonction = models.CharField(
        _('Fonction'),
        max_length=100,
        blank=True,
        help_text=_('Ex: Directeur, Responsable communication, Secrétaire'),
    )

    class Meta:
        verbose_name = _('Profil')
        verbose_name_plural = _('Profils')

    def __str__(self):
        return f"Profil de {self.user.username}"

    @property
    def nom_complet(self):
        """
        Retourne le nom complet de l'utilisateur, ou le username si non défini.
        """
        nom = self.user.get_full_name()
        return nom if nom else self.user.username

    @property
    def initiales(self):
        """
        Retourne les initiales pour l'avatar (ex: "JD" pour Jean Dupont).
        Utilisé quand pas de photo de profil.
        """
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        return self.user.username[:2].upper()

    @property
    def est_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def peut_editer(self):
        """L'utilisateur a les droits d'édition (super-admin ou éditeur)."""
        return self.role in [self.Role.SUPER_ADMIN, self.Role.EDITEUR]


# ============================================================
# SIGNAL : créer automatiquement un Profil pour chaque User
# ============================================================
@receiver(post_save, sender=User)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    """
    Signal Django : crée automatiquement un Profil quand un User est créé.

    Pourquoi un signal ?
    Sans cela, on devrait penser à créer manuellement un Profil
    à chaque création d'utilisateur. Avec le signal, c'est automatique
    et impossible à oublier.

    Concepts :
    - signal post_save : déclenché APRÈS la sauvegarde
    - sender=User : on écoute uniquement les saves du modèle User
    - @receiver : décorateur Django pour enregistrer la fonction comme listener
    - created=True : True uniquement si c'est une création (pas une mise à jour)
    """
    if created:
        # Premier user créé = super_admin (typiquement le développeur/directeur)
        role_initial = Profil.Role.SUPER_ADMIN if instance.is_superuser else Profil.Role.EDITEUR
        Profil.objects.create(user=instance, role=role_initial)


@receiver(post_save, sender=User)
def sauvegarder_profil_utilisateur(sender, instance, **kwargs):
    """
    Sauvegarde le profil quand le User est sauvegardé.
    Pratique pour synchroniser certains champs si besoin.
    """
    # Vérifie que le profil existe (cas des users créés AVANT ce signal)
    if hasattr(instance, 'profil'):
        instance.profil.save()
    else:
        # Cas legacy : crée le profil maintenant si manquant
        Profil.objects.get_or_create(user=instance)

