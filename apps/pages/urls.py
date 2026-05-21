from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    # /ecole/
    path('', views.ecole_view, name='ecole'),

    # /ecole/galerie/
    path('galerie/', views.galerie_view, name='galerie'),

    # /ecole/galerie/<slug>/
    path('galerie/<slug:slug>/', views.album_detail_view, name='album_detail'),
]