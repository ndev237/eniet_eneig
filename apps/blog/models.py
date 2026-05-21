from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Categorie(TimeStampedModel):
    """
    Catégorie d'article : Événement, Communiqué, Vie scolaire, Résultats, etc.

    Permet à l'admin de regrouper les articles thématiquement,
    et au visiteur de filtrer les actualités par sujet.
    """

    nom = models.CharField(
        _('Nom'),
        max_length=100,
        unique=True,
        help_text=_('Ex: Événement, Communiqué, Vie scolaire'),
    )

    slug = models.SlugField(
        _('Slug URL'),
        max_length=100,
        unique=True,
        help_text=_('Auto-généré depuis le nom si laissé vide'),
    )

    description = models.CharField(
        _('Description courte'),
        max_length=200,
        blank=True,
        help_text=_('Affichée sur la page de catégorie'),
    )

    # Couleur d'identification pour différencier visuellement les catégories
    # On utilisera ce champ pour appliquer des classes Tailwind dynamiquement
    couleur = models.CharField(
        _('Couleur'),
        max_length=20,
        choices=[
            ('primary', _('Vert (par défaut)')),
            ('accent', _('Or')),
            ('blue', _('Bleu')),
            ('red', _('Rouge')),
            ('purple', _('Violet')),
        ],
        default='primary',
        help_text=_('Couleur d\'affichage des badges de cette catégorie'),
    )

    ordre = models.PositiveSmallIntegerField(
        _('Ordre d\'affichage'),
        default=0,
    )

    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        """
        Génère automatiquement le slug à partir du nom si pas fourni.

        slugify() de Django transforme :
        - "Vie Scolaire" → "vie-scolaire"
        - "Événement spécial" → "evenement-special" (retire les accents)
        - Espaces → tirets, minuscules
        """
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})


class Tag(TimeStampedModel):
    """
    Tag : étiquette libre pour affiner la classification des articles.

    Différence avec Catégorie :
    - Catégorie = classification structurelle (1 par article)
    - Tag = mots-clés libres (plusieurs par article)

    Ex: un article "Cérémonie de remise des diplômes" peut avoir :
    - Catégorie : Événement
    - Tags : diplômes, promotion 2025, MINESEC, cérémonie
    """

    nom = models.CharField(
        _('Nom'),
        max_length=50,
        unique=True,
    )

    slug = models.SlugField(
        _('Slug URL'),
        max_length=50,
        unique=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})


class ArticleQuerySet(models.QuerySet):
    """
    Custom QuerySet : permet de définir des filtres réutilisables.

    Au lieu d'écrire partout :
        Article.objects.filter(statut='publie', date_publication__lte=now())

    On peut écrire :
        Article.objects.publies()

    Plus lisible, et si la logique de "publié" change un jour
    (ex: ajouter une condition), on modifie UN seul endroit.
    """

    def publies(self):
        """Retourne uniquement les articles publiés ET dont la date est passée."""
        return self.filter(
            statut=Article.Statut.PUBLIE,
            date_publication__lte=timezone.now(),
        )

    def en_avant(self):
        """Articles 'à la une' (mis en avant)."""
        return self.publies().filter(est_a_la_une=True)


class Article(TimeStampedModel):
    """
    Article de blog / actualité.

    C'est le modèle principal de cette phase. Il introduit plusieurs concepts :
    - ForeignKey vers User (auteur de l'article)
    - ForeignKey vers Categorie (un article a une catégorie)
    - ManyToMany vers Tag (un article peut avoir plusieurs tags)
    - Statut publié/brouillon (workflow éditorial)
    - Date de publication programmable (publier dans le futur)
    - Compteur de vues
    """

    class Statut(models.TextChoices):
        """Workflow éditorial : brouillon → publié → archivé."""
        BROUILLON = 'brouillon', _('Brouillon')
        PUBLIE = 'publie', _('Publié')
        ARCHIVE = 'archive', _('Archivé')

    # ============================================================
    # MANAGER PERSONNALISÉ
    # ============================================================
    # On remplace .objects par notre QuerySet custom
    # Permet d'utiliser Article.objects.publies() partout
    objects = ArticleQuerySet.as_manager()

    # ============================================================
    # CONTENU DE L'ARTICLE
    # ============================================================
    titre = models.CharField(
        _('Titre'),
        max_length=200,
    )

    slug = models.SlugField(
        _('Slug URL'),
        max_length=200,
        unique_for_date='date_publication',  # ← unique POUR UNE date donnée
        help_text=_('Auto-généré depuis le titre. Modifier avec prudence (URLs publiques)'),
    )

    resume = models.CharField(
        _('Résumé'),
        max_length=300,
        help_text=_('Phrase d\'accroche affichée sur la liste et les partages sociaux'),
    )

    contenu = models.TextField(
        _('Contenu'),
        help_text=_('Texte complet de l\'article. HTML autorisé.'),
    )

    # ============================================================
    # IMAGE À LA UNE
    # ============================================================
    image_une = models.ImageField(
        _('Image à la une'),
        upload_to='blog/articles/%Y/%m/',
        help_text=_('Image principale de l\'article. Format paysage recommandé.'),
    )

    image_une_alt = models.CharField(
        _('Texte alternatif image'),
        max_length=200,
        help_text=_('Description courte de l\'image (accessibilité, SEO)'),
    )

    # ============================================================
    # CLASSIFICATION (catégorie + tags)
    # ============================================================
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,  # ← Empêche la suppression d'une catégorie utilisée
        related_name='articles',
        verbose_name=_('Catégorie'),
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='articles',
        verbose_name=_('Tags'),
        help_text=_('Mots-clés pour affiner la recherche'),
    )

    # ============================================================
    # AUTEUR (lien vers User Django)
    # ============================================================
    auteur = models.ForeignKey(
        'auth.User',  # ← Référence au modèle User par chaîne (évite import circulaire)
        on_delete=models.SET_NULL,  # ← Si l'auteur est supprimé, l'article reste
        null=True,
        blank=True,
        related_name='articles',
        verbose_name=_('Auteur'),
    )

    # ============================================================
    # WORKFLOW ÉDITORIAL
    # ============================================================
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=Statut.choices,
        default=Statut.BROUILLON,
        help_text=_('Brouillon = invisible sur le site. Publié = visible.'),
    )

    date_publication = models.DateTimeField(
        _('Date de publication'),
        default=timezone.now,
        help_text=_('Date à partir de laquelle l\'article est visible. Permet de programmer une publication future.'),
    )

    # ============================================================
    # MISE EN AVANT
    # ============================================================
    est_a_la_une = models.BooleanField(
        _('À la une'),
        default=False,
        help_text=_('Mettre en avant cet article (homepage)'),
    )

    # ============================================================
    # MÉTRIQUES (statistiques pour le dashboard)
    # ============================================================
    nombre_vues = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0,
        editable=False,  # ← Pas modifiable dans l'admin (auto-géré)
    )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        # Tri par défaut : du plus récent au plus ancien
        ordering = ['-date_publication']
        # Index sur date_publication : accélère les requêtes filtrant par date
        indexes = [
            models.Index(fields=['-date_publication']),
            models.Index(fields=['statut', '-date_publication']),
        ]

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        """
        Génération automatique du slug si vide.
        IMPORTANT : on ne re-génère PAS le slug si l'article existe déjà
        pour éviter de casser les URLs publiques après publication.
        """
        if not self.slug:
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        URL canonique de l'article.

        Format : /actualites/2026/05/cérémonie-remise-diplomes/

        On inclut année + mois dans l'URL pour :
        1. Éviter les collisions de slugs entre années
        2. Améliorer le SEO (URL hiérarchique)
        3. Permettre l'archivage par date plus tard
        """
        return reverse('blog:detail', kwargs={
            'year': self.date_publication.year,
            'month': self.date_publication.month,
            'slug': self.slug,
        })

    @property
    def est_publie(self):
        """Indique si l'article est actuellement visible sur le site."""
        return (
                self.statut == self.Statut.PUBLIE
                and self.date_publication <= timezone.now()
        )

    def incrementer_vues(self):
        """
        Incrémente le compteur de vues de manière atomique.

        IMPORTANT : on utilise F() expression pour éviter les race conditions.
        Sans F(), si deux utilisateurs lisent l'article en même temps,
        on pourrait perdre un compteur.

        Avec F() :
        - Article.objects.filter(pk=1).update(nombre_vues=F('nombre_vues') + 1)
        - Génère SQL : UPDATE article SET nombre_vues = nombre_vues + 1 WHERE id = 1
        - Atomique au niveau base de données
        """
        from django.db.models import F
        # Update direct en BDD sans charger l'objet en mémoire
        Article.objects.filter(pk=self.pk).update(
            nombre_vues=F('nombre_vues') + 1
        )
        # On rafraîchit notre instance pour avoir la nouvelle valeur
        self.refresh_from_db(fields=['nombre_vues'])