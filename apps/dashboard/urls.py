from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dashboard'

urlpatterns = [
    # ============================================================
    # AUTHENTIFICATION
    # ============================================================
    # Django fournit LoginView qui gère tout : affichage du form, validation,
    # création de session, redirection. On surcharge juste le template.
    path('login/', auth_views.LoginView.as_view(template_name='dashboard/auth/login.html',redirect_authenticated_user=True,),name='login',),

    path('logout/', auth_views.LogoutView.as_view(template_name='dashboard/auth/logout.html',),name='logout',),

    # ============================================================
    # PAGES DU DASHBOARD
    # ============================================================
    path('', views.home, name='home'),
    # ============================================================
    # MODULE ARTICLES
    # ============================================================
    path('articles/', views.articles_list, name='articles_list'),
    path('articles/nouveau/', views.article_create, name='article_create'),
    path('articles/<int:pk>/modifier/', views.article_update, name='article_update'),
    path('articles/<int:pk>/supprimer/', views.article_delete, name='article_delete'),

    # Actions rapides
    path('articles/<int:pk>/toggle-publication/',
         views.article_toggle_publication,
         name='article_toggle_publication'),
    path('articles/<int:pk>/toggle-une/',
         views.article_toggle_une,
         name='article_toggle_une'),

    # Upload image TinyMCE
    path('tinymce/upload-image/', views.tinymce_upload_image, name='tinymce_upload_image'),

    # ============================================================
    # MODULE MESSAGES
    # ============================================================
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/repondre/', views.message_repondre, name='message_repondre'),
    path('messages/<int:pk>/note/', views.message_note, name='message_note'),
    path('messages/<int:pk>/statut/', views.message_changer_statut, name='message_changer_statut'),
    path('messages/<int:pk>/supprimer/', views.message_delete, name='message_delete'),

    # ============================================================
    # MODULE PARAMÈTRES
    # ============================================================
    path('parametres/', views.parametres, name='parametres'),

    # ============================================================
    # MODULE MÉDIAS / GALERIE
    # ============================================================
    path('medias/', views.medias_list, name='medias_list'),
    path('medias/nouveau/', views.album_create, name='album_create'),
    path('medias/<int:pk>/modifier/', views.album_edit, name='album_edit'),
    path('medias/<int:pk>/supprimer/', views.album_delete, name='album_delete'),

    # Endpoints AJAX pour les photos
    path('medias/<int:album_pk>/photos/upload/', views.photos_upload, name='photos_upload'),
    path('medias/<int:album_pk>/photos/reorder/', views.photos_reorder, name='photos_reorder'),
    path('medias/photos/<int:pk>/supprimer/', views.photo_delete, name='photo_delete'),
    path('medias/photos/<int:pk>/legende/', views.photo_update_legende, name='photo_update_legende'),

    # ============================================================
    # MODULE UTILISATEURS
    # ============================================================
    path('utilisateurs/', views.utilisateurs_list, name='utilisateurs_list'),
    path('utilisateurs/nouveau/', views.utilisateur_create, name='utilisateur_create'),
    path('utilisateurs/<int:pk>/modifier/', views.utilisateur_edit, name='utilisateur_edit'),
    path('utilisateurs/<int:pk>/mot-de-passe/', views.utilisateur_password, name='utilisateur_password'),
    path('utilisateurs/<int:pk>/toggle-actif/', views.utilisateur_toggle_actif, name='utilisateur_toggle_actif'),
    path('utilisateurs/<int:pk>/supprimer/', views.utilisateur_delete, name='utilisateur_delete'),

    # ============================================================
    # PROFIL PERSONNEL
    # ============================================================
    path('mon-profil/', views.mon_profil, name='mon_profil'),
    path('mon-profil/mot-de-passe/', views.mon_mot_de_passe, name='mon_mot_de_passe'),

]