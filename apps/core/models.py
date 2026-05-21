from django.db import models


class TimeStampedModel(models.Model):
    """
    Modèle abstrait fournissant les champs created_at et updated_at.

    Pourquoi abstrait ? Parce qu'on ne veut PAS créer de table 'TimeStampedModel'
    en BDD. On veut juste que d'autres modèles héritent de ces deux champs.
    L'option `abstract = True` dans Meta dit à Django : "ce modèle est un parent,
    pas une vraie table".

    Utilisation :
        class Article(TimeStampedModel):
            titre = models.CharField(max_length=200)
            # Hérite automatiquement de created_at et updated_at
    """

    # auto_now_add=True : rempli automatiquement à la CRÉATION uniquement
    # Ne change jamais après. Type DateTime avec timezone (selon USE_TZ=True dans settings)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création',
    )

    # auto_now=True : mis à jour automatiquement à chaque SAVE
    # Très utile pour traquer la dernière modification d'un objet
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière modification',
    )

    class Meta:
        abstract = True  # ← Pas de table créée pour ce modèle