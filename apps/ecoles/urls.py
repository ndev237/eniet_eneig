from django.urls import path

from . import views

app_name = 'ecoles'

urlpatterns = [
    # /formations/
    path('', views.formations_list_view, name='formations_list'),

    # /formations/admission/ - placé AVANT le pattern slug pour matcher en premier
    path('admission/', views.admission_view, name='admission'),

    # /formations/<ecole>/
    path('<slug:ecole_slug>/', views.ecole_detail_view, name='ecole_detail'),

    # /formations/<ecole>/<filiere>/
    path('<slug:ecole_slug>/<slug:filiere_slug>/', views.filiere_detail_view, name='filiere_detail'),
]