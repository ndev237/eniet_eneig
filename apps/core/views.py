from django.shortcuts import render

def home(request):
    """Page d'accueil du site ENIET/ENIEG."""
    return render(request, 'core/home.html')