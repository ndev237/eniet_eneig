from django.shortcuts import render

from apps.blog.models import Article
from apps.ecoles.models import Ecole


def home(request):
    """
    Page d'accueil.

    - 3 derniers articles publiés à mettre en avant.
    - Récupère les deux écoles (ENIEG + ENIET) pour générer les liens
      « En savoir plus » des cartes du bloc « Deux écoles ».
    """
    derniers_articles = Article.objects.publies().select_related(
        'categorie'
    )[:3]

    # Récupération par sigle — robuste si l'ordre des Ecole change en BDD.
    # `.filter().first()` plutôt que `.get()` pour ne pas planter si l'objet manque
    # (la carte affiche tout sauf le lien si l'école n'est pas renseignée).
    ecole_enieg = Ecole.objects.filter(sigle__iexact='ENIEG').first()
    ecole_eniet = Ecole.objects.filter(sigle__iexact='ENIET').first()

    return render(request, 'core/home.html', {
        'derniers_articles': derniers_articles,
        'ecole_enieg': ecole_enieg,
        'ecole_eniet': ecole_eniet,
    })