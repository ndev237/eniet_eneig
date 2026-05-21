from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class SiteSettings(TimeStampedModel):
    """
    Paramètres globaux du site - PATTERN SINGLETON.

    Qu'est-ce qu'un singleton ?
    Un singleton est un modèle dont on ne veut AUTORISER qu'UNE SEULE
    instance en base de données. Ici, les "paramètres du site" sont
    par définition uniques : il n'y a qu'un seul site, donc qu'un seul
    ensemble de paramètres.

    Pourquoi cette approche ?
    - L'admin modifie l'email, le téléphone, l'adresse depuis le dashboard
    - On ne veut pas recompiler/redéployer pour ces changements
    - Tous les templates peuvent afficher {{ settings.email }} dynamiquement

    Comment forcer l'unicité ?
    On surcharge la méthode save() pour empêcher la création d'un 2e objet.
    """

    # ============================================================
    # IDENTITÉ DE L'ÉTABLISSEMENT
    # ============================================================
    nom_etablissement = models.CharField(
        _('Nom de l\'établissement'),
        max_length=200,
        default='ENIET / ENIEG de l\'Excellence Professionnelle',
        help_text=_('Affiché dans le footer et les emails'),
    )

    devise = models.CharField(
        _('Devise'),
        max_length=200,
        default='Excellence Professionnelle',
        blank=True,
    )

    description_courte = models.TextField(
        _('Description courte'),
        max_length=500,
        default='École Normale d\'Instituteurs de l\'Enseignement Général et Technique. Établissement agréé par le MINESEC.',
        help_text=_('Utilisée dans le footer et les méta-descriptions par défaut'),
    )

    # ============================================================
    # COORDONNÉES
    # ============================================================
    email_principal = models.EmailField(
        _('Email principal'),
        default='efpsaf@yahoo.fr',
    )

    email_contact = models.EmailField(
        _('Email de contact'),
        default='efpsaf@yahoo.fr',
        help_text=_('Email qui reçoit les messages du formulaire de contact'),
    )

    telephone_1 = models.CharField(
        _('Téléphone principal'),
        max_length=30,
        default='+237 696 16 20 16',
    )

    telephone_2 = models.CharField(
        _('Téléphone secondaire'),
        max_length=30,
        default='+237 672 46 70 70',
        blank=True,
    )

    telephone_3 = models.CharField(
        _('Téléphone 3'),
        max_length=30,
        default='+237 678 46 96 64',
        blank=True,
    )

    adresse_ligne_1 = models.CharField(
        _('Adresse - ligne 1'),
        max_length=200,
        default='Yassa, Entrée Planète Voyage',
    )

    adresse_ligne_2 = models.CharField(
        _('Adresse - ligne 2'),
        max_length=200,
        default='Douala, Cameroun',
        blank=True,
    )

    boite_postale = models.CharField(
        _('Boîte postale'),
        max_length=50,
        default='BP 4100 Douala',
        blank=True,
    )

    # ============================================================
    # COORDONNÉES GPS POUR LA CARTE
    # ============================================================
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=10,
        decimal_places=7,
        default=4.0511,
        help_text=_('Coordonnée GPS pour la carte (ex: 4.0511 pour Douala)'),
    )

    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=10,
        decimal_places=7,
        default=9.7547,
        help_text=_('Coordonnée GPS pour la carte'),
    )

    # ============================================================
    # HORAIRES D'OUVERTURE (champs simples pour MVP)
    # ============================================================
    horaires_semaine = models.CharField(
        _('Horaires lundi-vendredi'),
        max_length=100,
        default='07h30 — 17h00',
        blank=True,
    )

    horaires_samedi = models.CharField(
        _('Horaires samedi'),
        max_length=100,
        default='08h00 — 13h00',
        blank=True,
    )

    # ============================================================
    # RÉSEAUX SOCIAUX
    # ============================================================
    facebook_url = models.URLField(_('URL Facebook'), blank=True)
    instagram_url = models.URLField(_('URL Instagram'), blank=True)
    youtube_url = models.URLField(_('URL YouTube'), blank=True)
    linkedin_url = models.URLField(_('URL LinkedIn'), blank=True)

    # ============================================================
    # AGRÉMENTS OFFICIELS
    # ============================================================
    arrete_eniet = models.CharField(
        _('N° arrêté ENIET'),
        max_length=100,
        default='n°69/15/MINESEC/SEESEN/SG/DPN/SDENT/SGENPRI du 21 Avril 2015',
        blank=True,
    )

    arrete_enieg = models.CharField(
        _('N° arrêté ENIEG'),
        max_length=100,
        default='n°26/15/MINESEC/SEESEN/SG/DEN/SDENG/SSGENPRI du 27 Janvier 2015',
        blank=True,
    )

    # ============================================================
    # ANNÉE SCOLAIRE / CONCOURS EN COURS
    # ============================================================
    annee_scolaire = models.CharField(
        _('Année scolaire en cours'),
        max_length=20,
        default='2025-2026',
        help_text=_('Format : YYYY-YYYY'),
    )

    class Meta:
        verbose_name = _('Paramètre du site')
        verbose_name_plural = _('Paramètres du site')

    def __str__(self):
        return f"Paramètres du site ({self.nom_etablissement})"

    def save(self, *args, **kwargs):
        """
        Surcharge de save() pour FORCER l'unicité (pattern singleton).

        Au lieu de créer un nouvel objet, on force toujours pk=1.
        Si un objet avec pk=1 existe déjà, on le met à jour.
        Si on essaie de créer un 2e objet, save() écrasera le 1er.
        """
        self.pk = 1  # ← clé primaire forcée à 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        On empêche la suppression accidentelle des paramètres.
        Si un admin clique sur "supprimer", rien ne se passe.
        """
        pass

    @classmethod
    def load(cls):
        """
        Méthode de classe pour récupérer l'instance unique.
        Si elle n'existe pas, la crée avec les valeurs par défaut.

        Utilisation :
            settings = SiteSettings.load()
            print(settings.email_principal)
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Valeur(TimeStampedModel):
    """
    Une valeur de l'établissement (excellence, rigueur, intégrité, etc.).
    Affichée sur la page "L'École" pour humaniser l'institution.
    """

    titre = models.CharField(
        _('Titre de la valeur'),
        max_length=100,
        help_text=_('Ex: Excellence, Rigueur, Intégrité'),
    )

    description = models.TextField(
        _('Description'),
        help_text=_('Courte description de la valeur'),
    )

    icone = models.CharField(
        _('Icône SVG path'),
        max_length=10,
        default='star',
        help_text=_('Identifiant d\'icône : star, shield, heart, book, etc.'),
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text=_('Plus le nombre est petit, plus la valeur apparaît en premier'),
    )

    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Décocher pour masquer cette valeur sans la supprimer'),
    )

    class Meta:
        verbose_name = _('Valeur de l\'établissement')
        verbose_name_plural = _('Valeurs de l\'établissement')
        # ordering : trié par champ ordre, puis par date de création si égalité
        ordering = ['ordre', 'created_at']

    def __str__(self):
        return self.titre


class MembreDirection(TimeStampedModel):
    """
    Membre de l'équipe dirigeante affiché sur la page "L'École".
    Le directeur, le directeur des études, etc.
    """

    nom = models.CharField(_('Nom complet'), max_length=150)

    fonction = models.CharField(
        _('Fonction'),
        max_length=150,
        help_text=_('Ex: Directeur, Directeur des Études, Censeur'),
    )

    biographie = models.TextField(
        _('Biographie'),
        blank=True,
        help_text=_('Courte biographie / parcours professionnel'),
    )

    citation = models.TextField(
        _('Citation / Mot'),
        blank=True,
        help_text=_('Citation à afficher (notamment pour le directeur)'),
    )

    photo = models.ImageField(
        _('Photo'),
        upload_to='equipe/',
        blank=True,
        null=True,
        help_text=_('Photo professionnelle - format carré recommandé'),
    )

    # Mise en avant - le directeur aura est_directeur=True
    # pour être affiché en grand avec sa citation
    est_directeur = models.BooleanField(
        _('Est le directeur'),
        default=False,
        help_text=_('Cochez pour le directeur principal (affichage spécial)'),
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    actif = models.BooleanField(_('Actif'), default=True)

    class Meta:
        verbose_name = _('Membre de la direction')
        verbose_name_plural = _('Membres de la direction')
        ordering = ['ordre', 'created_at']

    def __str__(self):
        return f"{self.nom} ({self.fonction})"


class Album(TimeStampedModel):
    """
    Album photo : regroupe plusieurs photos sur un thème.
    Ex: 'Cérémonie de remise des diplômes 2025', 'Visite ministérielle', etc.
    """

    titre = models.CharField(
        _('Titre de l\'album'),
        max_length=200,
    )

    slug = models.SlugField(
        _('Slug URL'),
        max_length=200,
        unique=True,
        help_text=_('Identifiant pour l\'URL (généré automatiquement)'),
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Présentation de l\'événement, contexte'),
    )

    date_evenement = models.DateField(
        _('Date de l\'événement'),
        help_text=_('Date à laquelle l\'événement a eu lieu'),
    )

    # Photo de couverture : utilisée sur la grille des albums
    # Si non définie, on prendra automatiquement la 1ère photo de l'album
    couverture = models.ImageField(
        _('Photo de couverture'),
        upload_to='galerie/couvertures/',
        blank=True,
        null=True,
        help_text=_('Optionnel - si vide, on utilise la 1ère photo de l\'album'),
    )

    # Mettre en avant un album sur la page d'accueil par exemple
    est_a_la_une = models.BooleanField(
        _('À la une'),
        default=False,
        help_text=_('Mettre en avant cet album'),
    )

    publie = models.BooleanField(
        _('Publié'),
        default=True,
        help_text=_('Décocher pour cacher l\'album sans le supprimer'),
    )

    class Meta:
        verbose_name = _('Album photo')
        verbose_name_plural = _('Albums photos')
        # Tri par date d'événement décroissante : les plus récents en premier
        ordering = ['-date_evenement', '-created_at']

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('pages:album_detail', kwargs={'slug': self.slug})

    @property
    def couverture_url(self):
        """
        Retourne l'URL de la couverture, ou de la 1ère photo si pas de couverture.

        Utilisation dans les templates :
            <img src="{{ album.couverture_url }}">
        au lieu de :
            {% if album.couverture %}{{ album.couverture.url }}{% else %}...{% endif %}
        """
        if self.couverture:
            return self.couverture.url
        # Pas de couverture définie → on prend la 1ère photo
        # .first() retourne None si l'album est vide
        premiere_photo = self.photos.first()
        if premiere_photo:
            return premiere_photo.image.url
        # Aucune photo dans l'album : on retourne None
        # Le template gérera ce cas avec un placeholder
        return None

    @property
    def nombre_photos(self):
        """Compte le nombre de photos dans l'album (utile pour l'affichage)."""
        return self.photos.count()


class Photo(TimeStampedModel):
    """
    Une photo individuelle appartenant à un album.
    """

    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,  # Si l'album est supprimé, ses photos aussi
        related_name='photos',
        verbose_name=_('Album'),
    )

    image = models.ImageField(
        _('Image'),
        upload_to='galerie/photos/%Y/%m/',  # Stockage par année/mois
        help_text=_('Format JPG ou PNG, taille recommandée : 1920x1080 max'),
    )

    # Légende facultative affichée sous la photo dans le lightbox
    legende = models.CharField(
        _('Légende'),
        max_length=300,
        blank=True,
        help_text=_('Description de la photo (visible au survol et dans le lightbox)'),
    )

    # Alt obligatoire pour l'accessibilité
    alt = models.CharField(
        _('Texte alternatif'),
        max_length=200,
        help_text=_('Description courte pour les lecteurs d\'écran (accessibilité)'),
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text=_('Plus le nombre est petit, plus la photo apparaît en premier'),
    )

    class Meta:
        verbose_name = _('Photo')
        verbose_name_plural = _('Photos')
        ordering = ['ordre', 'created_at']

    def __str__(self):
        return f"{self.album.titre} - {self.legende | default:'Photo'}"