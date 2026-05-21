from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Ecole(TimeStampedModel):
    """
    Représente une école du complexe : ENIEG ou ENIET.

    Chaque école a :
    - Son nom, son sigle, son diplôme préparé
    - Ses propres tranches de paiement (ForeignKey inverse depuis TranchePaiement)
    - Ses filières spécifiques (pour ENIET uniquement, ForeignKey depuis Filiere)
    """

    class TypeEcole(models.TextChoices):
        """Type d'enseignement : Général ou Technique."""
        GENERAL = 'general', _('Enseignement Général')
        TECHNIQUE = 'technique', _('Enseignement Technique')

    # ============================================================
    # IDENTITÉ DE L'ÉCOLE
    # ============================================================
    nom = models.CharField(
        _('Nom complet'),
        max_length=200,
        help_text=_('Ex: École Normale d\'Instituteurs de l\'Enseignement Général'),
    )

    sigle = models.CharField(
        _('Sigle'),
        max_length=10,
        unique=True,  # ← unique=True : empêche deux écoles avec le même sigle
        help_text=_('Ex: ENIEG ou ENIET'),
    )

    # slug : version "URL-friendly" du sigle pour les URLs propres
    # /admission/enieg/ au lieu de /admission/1/
    slug = models.SlugField(
        _('Slug URL'),
        max_length=20,
        unique=True,
        help_text=_('Identifiant pour l\'URL, en minuscules sans accents'),
    )

    type_ecole = models.CharField(
        _('Type'),
        max_length=20,
        choices=TypeEcole.choices,
    )

    diplome_prepare = models.CharField(
        _('Diplôme préparé'),
        max_length=100,
        help_text=_('Ex: CAPIEMP ou CAPIET'),
    )

    diplome_complet = models.CharField(
        _('Intitulé complet du diplôme'),
        max_length=300,
        help_text=_('Ex: Certificat d\'Aptitude Pédagogique d\'Instituteurs...'),
    )

    description_courte = models.TextField(
        _('Description courte'),
        max_length=500,
        help_text=_('Affichée sur la page d\'accueil et la liste des écoles'),
    )

    description_longue = models.TextField(
        _('Description détaillée'),
        blank=True,
        help_text=_('Affichée sur la page admission de l\'école'),
    )

    # ============================================================
    # CONDITIONS D'ADMISSION
    # ============================================================
    pre_requis = models.TextField(
        _('Pré-requis d\'admission'),
        help_text=_('Diplômes acceptés : Bac, BT, BP, etc.'),
    )

    duree_formation = models.CharField(
        _('Durée de la formation'),
        max_length=50,
        default='2 ans',
    )

    # ============================================================
    # FRAIS - Champs simples pour l'inscription et le concours
    # Les tranches sont dans un modèle séparé (relation 1-N)
    # ============================================================
    frais_concours = models.PositiveIntegerField(
        _('Frais de concours (FCFA)'),
        default=12000,
        help_text=_('Frais d\'inscription au concours, non remboursables'),
    )

    frais_inscription_non_remboursable = models.PositiveIntegerField(
        _('Inscription non remboursable (FCFA)'),
        default=25000,
    )

    matiere_oeuvre = models.PositiveIntegerField(
        _('Matière d\'œuvre (FCFA)'),
        default=0,
        help_text=_('Frais de matière d\'œuvre - 0 pour ENIEG, 25000 pour ENIET'),
    )

    # ============================================================
    # AFFICHAGE
    # ============================================================
    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    actif = models.BooleanField(_('Actif'), default=True)

    class Meta:
        verbose_name = _('École')
        verbose_name_plural = _('Écoles')
        ordering = ['ordre', 'sigle']

    def __str__(self):
        return self.sigle

    @property
    def total_premiere_annee(self):
        """
        Calcule automatiquement le total de la 1ère année.

        Utilise la relation inverse : self.tranches.filter(annee=1)
        Django crée automatiquement cet accès depuis la ForeignKey
        définie dans TranchePaiement.
        """
        # aggregate() permet de faire SUM, AVG, COUNT directement en SQL
        # plus performant que de tout charger en mémoire puis sommer
        from django.db.models import Sum
        total_tranches = self.tranches.filter(annee=1).aggregate(
            total=Sum('montant')
        )['total'] or 0

        return (
                self.frais_inscription_non_remboursable
                + self.matiere_oeuvre
                + total_tranches
        )


class TranchePaiement(TimeStampedModel):
    """
    Une tranche de paiement de la scolarité.

    RELATION CLÉ : ForeignKey vers Ecole

    Une école a PLUSIEURS tranches (1ère tranche à l'inscription,
    2ème tranche en décembre, etc.) → on dit que c'est une relation
    "one-to-many" (un vers plusieurs).

    En BDD : la table TranchePaiement aura une colonne 'ecole_id'
    qui pointe vers la table Ecole.

    Côté Python :
    - tranche.ecole  → l'école associée
    - ecole.tranches.all()  → toutes les tranches (relation inverse)
                              ← définie par related_name='tranches'
    """

    # ============================================================
    # RELATION VERS L'ÉCOLE
    # ============================================================
    ecole = models.ForeignKey(
        Ecole,
        on_delete=models.CASCADE,  # Si l'école est supprimée, ses tranches aussi
        related_name='tranches',  # ← permet ecole.tranches.all()
        verbose_name=_('École'),
    )

    # ============================================================
    # IDENTIFICATION DE LA TRANCHE
    # ============================================================
    annee = models.PositiveSmallIntegerField(
        _('Année de scolarité'),
        choices=[(1, _('1ère année')), (2, _('2ème année'))],
        help_text=_('À quelle année concerne cette tranche'),
    )

    numero_tranche = models.PositiveSmallIntegerField(
        _('Numéro de tranche'),
        help_text=_('1 pour la 1ère tranche, 2 pour la 2ème, etc.'),
    )

    libelle = models.CharField(
        _('Libellé'),
        max_length=100,
        help_text=_('Ex: "1ère tranche", "2ème tranche"'),
    )

    montant = models.PositiveIntegerField(
        _('Montant (FCFA)'),
    )

    echeance = models.CharField(
        _('Échéance'),
        max_length=100,
        help_text=_('Ex: "À l\'inscription", "Le 10 décembre"'),
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    class Meta:
        verbose_name = _('Tranche de paiement')
        verbose_name_plural = _('Tranches de paiement')
        ordering = ['ecole', 'annee', 'numero_tranche']
        # unique_together : empêche deux tranches identiques pour la même école
        # Ex: pas deux "1ère tranche année 1" pour ENIEG
        unique_together = [['ecole', 'annee', 'numero_tranche']]

    def __str__(self):
        return f"{self.ecole.sigle} - {self.libelle} (année {self.annee}) : {self.montant} FCFA"


class DocumentRequis(TimeStampedModel):
    """
    Document obligatoire pour le dossier de candidature.

    Modèle GLOBAL (pas lié à une école spécifique) car les documents
    sont les mêmes pour ENIEG et ENIET d'après les PDF officiels.
    Si jamais cela diffère plus tard, on pourra ajouter une ForeignKey.
    """

    libelle = models.CharField(
        _('Document'),
        max_length=200,
        help_text=_('Ex: "Photocopie CNI"'),
    )

    description = models.CharField(
        _('Précision'),
        max_length=300,
        blank=True,
        help_text=_('Détails optionnels (format, exigences...)'),
    )

    obligatoire = models.BooleanField(
        _('Obligatoire'),
        default=True,
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    class Meta:
        verbose_name = _('Document requis')
        verbose_name_plural = _('Documents requis')
        ordering = ['ordre', 'libelle']

    def __str__(self):
        return self.libelle


class FAQ(TimeStampedModel):
    """
    Question fréquemment posée sur l'admission.

    Note pédagogique :
    Le nom 'FAQ' viole légèrement la convention Django (singulier)
    mais c'est l'usage courant pour ce type de contenu.
    """

    class Categorie(models.TextChoices):
        ADMISSION = 'admission', _('Admission')
        FORMATION = 'formation', _('Formation')
        FRAIS = 'frais', _('Frais et paiement')
        AUTRE = 'autre', _('Autre')

    question = models.CharField(
        _('Question'),
        max_length=300,
    )

    reponse = models.TextField(
        _('Réponse'),
    )

    categorie = models.CharField(
        _('Catégorie'),
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.ADMISSION,
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    actif = models.BooleanField(_('Actif'), default=True)

    class Meta:
        verbose_name = _('Question fréquente')
        verbose_name_plural = _('Questions fréquentes')
        ordering = ['categorie', 'ordre']

    def __str__(self):
        return self.question[:80]


class Filiere(TimeStampedModel):
    """
    Une filière de formation au sein d'une école.

    Pour ENIEG : généralement pas de filières (formation générale unique).
    Pour ENIET : 7 filières techniques distinctes.

    RELATIONS :
    - Une Filiere appartient à UNE Ecole (ForeignKey)
    - Une Ecole peut avoir PLUSIEURS Filieres (relation inverse)
    """

    # ============================================================
    # RELATION VERS L'ÉCOLE
    # ============================================================
    ecole = models.ForeignKey(
        Ecole,
        on_delete=models.CASCADE,
        related_name='filieres',  # → ecole.filieres.all()
        verbose_name=_('École'),
    )

    # ============================================================
    # IDENTITÉ DE LA FILIÈRE
    # ============================================================
    nom = models.CharField(
        _('Nom de la filière'),
        max_length=150,
        help_text=_('Ex: Électricité, Couture, Bureautique'),
    )

    slug = models.SlugField(
        _('Slug URL'),
        max_length=50,
        help_text=_('Identifiant pour l\'URL (sans accent, en minuscules)'),
    )

    description_courte = models.CharField(
        _('Description courte'),
        max_length=250,
        help_text=_('Phrase d\'accroche affichée sur les cartes'),
    )

    description_longue = models.TextField(
        _('Description détaillée'),
        blank=True,
        help_text=_('Présentation complète, affichée sur la page de détail'),
    )

    # ============================================================
    # CONTENU PÉDAGOGIQUE
    # ============================================================
    debouches = models.TextField(
        _('Débouchés professionnels'),
        blank=True,
        help_text=_('Métiers et opportunités après la formation'),
    )

    competences_acquises = models.TextField(
        _('Compétences acquises'),
        blank=True,
        help_text=_('Une compétence par ligne'),
    )

    matieres_principales = models.TextField(
        _('Matières principales'),
        blank=True,
        help_text=_('Une matière par ligne'),
    )

    # ============================================================
    # IDENTIFICATION VISUELLE
    # ============================================================
    icone = models.CharField(
        _('Icône'),
        max_length=20,
        default='briefcase',
        help_text=_('Identifiant d\'icône : bolt, building, scissors, chart, computer...'),
    )

    image = models.ImageField(
        _('Image illustrative'),
        upload_to='filieres/',
        blank=True,
        null=True,
        help_text=_('Photo d\'illustration de la filière'),
    )

    # ============================================================
    # AFFICHAGE
    # ============================================================
    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    actif = models.BooleanField(_('Actif'), default=True)

    class Meta:
        verbose_name = _('Filière')
        verbose_name_plural = _('Filières')
        ordering = ['ecole', 'ordre', 'nom']
        # unique_together : empêche deux filières avec le même slug dans la même école
        unique_together = [['ecole', 'slug']]

    def __str__(self):
        return f"{self.ecole.sigle} - {self.nom}"

    def get_absolute_url(self):
        """
        Retourne l'URL canonique de cette filière.

        ÉLÉGANT : Django va construire automatiquement l'URL en utilisant
        le nom de l'URL défini dans urls.py et les paramètres slug.

        Avantage : si on change la structure des URLs plus tard,
        on modifie UN SEUL endroit (urls.py) au lieu de chercher
        partout où on construit l'URL à la main.

        Utilisation dans les templates : <a href="{{ filiere.get_absolute_url }}">
        """
        from django.urls import reverse
        return reverse('ecoles:filiere_detail', kwargs={
            'ecole_slug': self.ecole.slug,
            'filiere_slug': self.slug,
        })