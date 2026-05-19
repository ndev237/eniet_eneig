from django.urls import path
from . import views

# app_name permet de namespacer les URLs : {% url 'core:home' %}
# Évite les conflits si plusieurs apps ont une URL 'home'
app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
]