from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.views.decorators.http import require_GET

from .models import Article, Categorie, Tag

# ============================================================
# CONSTANTES DE CONFIGURATION
# ============================================================
ARTICLES_PAR_PAGE = 9  # Nombre d'articles par page (multiple de 3 pour la grille)


def article_list(request):
    """
    Liste paginée des articles publiés.

    Gère 3 fonctionnalités combinables :
    1. Filtrage par catégorie (paramètre GET ?categorie=evenement)
    2. Filtrage par tag (?tag=concours)
    3. Recherche textuelle (?q=mot-cle)

    Pourquoi ces filtres en GET et pas en POST ?
    - URLs bookmarkables : un visiteur peut partager le lien d'une recherche
    - Référencement SEO : Google peut indexer ces pages
    - Retour navigateur fonctionnel
    """

    # ============================================================
    # 1. QUERYSET DE BASE : tous les articles publiés
    # ============================================================
    # On utilise notre QuerySet custom .publies() défini dans models.py
    # select_related : optimise la requête en faisant une jointure SQL
    #                  pour récupérer la catégorie en une seule requête
    # prefetch_related : pour les tags (ManyToMany = 2 requêtes)
    queryset = Article.objects.publies().select_related(
        'categorie', 'auteur'
    ).prefetch_related('tags')

    # ============================================================
    # 2. FILTRAGE PAR CATÉGORIE
    # ============================================================
    # request.GET.get('nom') retourne None si pas de paramètre
    # plus sûr que request.GET['nom'] qui lèverait KeyError
    categorie_slug = request.GET.get('categorie')
    categorie_active = None

    if categorie_slug:
        # On essaie de récupérer la catégorie pour validation
        # Si elle n'existe pas, on ignore le filtre (pas d'erreur)
        try:
            categorie_active = Categorie.objects.get(slug=categorie_slug)
            queryset = queryset.filter(categorie=categorie_active)
        except Categorie.DoesNotExist:
            pass

    # ============================================================
    # 3. FILTRAGE PAR TAG
    # ============================================================
    tag_slug = request.GET.get('tag')
    tag_active = None

    if tag_slug:
        try:
            tag_active = Tag.objects.get(slug=tag_slug)
            # tags__in : filtre les articles ayant ce tag (relation M2M)
            queryset = queryset.filter(tags=tag_active)
        except Tag.DoesNotExist:
            pass

    # ============================================================
    # 4. RECHERCHE TEXTUELLE
    # ============================================================
    # Q objects permettent les conditions OU (par défaut Django fait des ET)
    # On cherche dans plusieurs champs : titre, résumé, contenu
    recherche = request.GET.get('q', '').strip()

    if recherche:
        # __icontains : insensible à la casse, recherche partielle
        # ex: recherche="diplo" trouve "Diplôme", "Diplomatie", etc.
        queryset = queryset.filter(
            Q(titre__icontains=recherche)
            | Q(resume__icontains=recherche)
            | Q(contenu__icontains=recherche)
        ).distinct()  # distinct() évite les doublons si l'article matche plusieurs Q

    # ============================================================
    # 5. PAGINATION
    # ============================================================
    # Paginator divise le QuerySet en pages de N éléments
    paginator = Paginator(queryset, ARTICLES_PAR_PAGE)

    # Récupère le numéro de page depuis l'URL (?page=2)
    # Par défaut : page 1
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # ?page=abc → on revient à la page 1
        page_obj = paginator.page(1)
    except EmptyPage:
        # ?page=99 (n'existe pas) → on affiche la dernière page
        page_obj = paginator.page(paginator.num_pages)

    # ============================================================
    # 6. DONNÉES ANNEXES pour la sidebar et les filtres
    # ============================================================
    # Toutes les catégories avec le compte de leurs articles publiés
    # annotate + Count : ajoute un champ calculé "nb_articles"
    categories = Categorie.objects.annotate(
        nb_articles=Count('articles', filter=Q(articles__statut='publie'))
    ).filter(nb_articles__gt=0).order_by('ordre')

    # Tags populaires (les plus utilisés sur les articles publiés)
    # On limite à 12 pour ne pas surcharger la sidebar
    tags_populaires = Tag.objects.annotate(
        nb_articles=Count('articles', filter=Q(articles__statut='publie'))
    ).filter(nb_articles__gt=0).order_by('-nb_articles')[:12]

    # ============================================================
    # 7. CONTEXTE TEMPLATE
    # ============================================================
    return render(request, 'blog/list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'tags_populaires': tags_populaires,
        'categorie_active': categorie_active,
        'tag_active': tag_active,
        'recherche': recherche,
        # On passe le compte total pour l'afficher dans le hero
        'total_articles': paginator.count,
    })


def article_detail(request, year, month, slug):
    """
    Détail d'un article spécifique.

    L'URL contient l'année et le mois pour éviter les collisions
    de slugs et pour le SEO (URL hiérarchique).

    Pourquoi 3 paramètres dans l'URL ?
    Article.slug est unique_for_date='date_publication',
    donc on a besoin de la date pour identifier l'article de manière unique.
    """

    # Récupération de l'article publié uniquement
    # date_publication__year et __month sont des "field lookups" Django :
    # ils extraient l'année/mois directement en SQL
    article = get_object_or_404(
        Article.objects.publies().select_related('categorie', 'auteur').prefetch_related('tags'),
        date_publication__year=year,
        date_publication__month=month,
        slug=slug,
    )

    # ============================================================
    # INCRÉMENTATION DU COMPTEUR DE VUES
    # ============================================================
    # On utilise la méthode atomique définie sur le modèle
    article.incrementer_vues()

    # ============================================================
    # ARTICLES SIMILAIRES
    # ============================================================
    # Logique : articles publiés, même catégorie, sauf celui-ci, max 3
    # Si on a moins de 3 articles dans la catégorie, on complète avec
    # d'autres articles récents
    articles_similaires = Article.objects.publies().filter(
        categorie=article.categorie,
    ).exclude(pk=article.pk).order_by('-date_publication')[:3]

    # Si on n'a pas 3 articles similaires, on complète avec des récents
    if articles_similaires.count() < 3:
        # exclude(pk__in=...) : exclut les articles déjà sélectionnés ET l'article courant
        deja_selectionnes = list(articles_similaires.values_list('pk', flat=True))
        deja_selectionnes.append(article.pk)

        complement = Article.objects.publies().exclude(
            pk__in=deja_selectionnes
        ).order_by('-date_publication')[:3 - articles_similaires.count()]

        # On combine les deux QuerySets en une liste
        articles_similaires = list(articles_similaires) + list(complement)

    return render(request, 'blog/detail.html', {
        'article': article,
        'articles_similaires': articles_similaires,
    })


def category_view(request, slug):
    """
    Liste des articles d'une catégorie spécifique.

    Stratégie : on délègue à article_list en injectant le paramètre.
    Plutôt que de dupliquer toute la logique de pagination/recherche.
    """
    # On vérifie d'abord que la catégorie existe (404 sinon)
    categorie = get_object_or_404(Categorie, slug=slug)

    # Astuce : on modifie une copie de request.GET pour ajouter le paramètre
    # request.GET est immuable par défaut, on doit faire .copy()
    request.GET = request.GET.copy()
    request.GET['categorie'] = slug

    return article_list(request)


def tag_view(request, slug):
    """
    Liste des articles d'un tag spécifique.
    Même stratégie que category_view.
    """
    tag = get_object_or_404(Tag, slug=slug)

    request.GET = request.GET.copy()
    request.GET['tag'] = slug

    return article_list(request)