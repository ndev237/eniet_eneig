from django.shortcuts import render

from apps.blog.models import Article


def home(request):
    """
    Page d'accueil.

    Récupère les 3 derniers articles publiés à mettre en avant.
    """
    # 3 derniers articles publiés (à la une en priorité, sinon les plus récents)
    # ManagerCustom : .objects.publies() filtre déjà sur statut + date
    derniers_articles = Article.objects.publies().select_related(
        'categorie'
    )[:3]

    return render(request, 'core/home.html', {
        'derniers_articles': derniers_articles,
    })