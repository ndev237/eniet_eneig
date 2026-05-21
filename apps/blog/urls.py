from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    # /actualites/ - Liste paginée (avec filtres GET optionnels)
    path('', views.article_list, name='list'),

    # /actualites/categorie/<slug>/ - Articles d'une catégorie
    path('categorie/<slug:slug>/', views.category_view, name='category'),

    # /actualites/tag/<slug>/ - Articles d'un tag
    path('tag/<slug:slug>/', views.tag_view, name='tag'),

    # /actualites/2026/05/ceremonie-diplomes/ - Détail d'un article
    # Les <int:year> et <int:month> capturent des entiers
    # <slug:slug> capture une chaîne alphanumérique
    path('<int:year>/<int:month>/<slug:slug>/', views.article_detail,name='detail',),
]