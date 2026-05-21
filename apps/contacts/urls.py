from django.urls import path

from . import views

# Namespace : permet d'éviter les conflits si plusieurs apps ont une URL 'contact'
# Usage : {% url 'contacts:contact' %} au lieu de {% url 'contact' %}
app_name = 'contacts'

urlpatterns = [
    path('', views.contact_view, name='contact'),
]