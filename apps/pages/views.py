from django.shortcuts import render, get_object_or_404

from .models import Valeur, MembreDirection, Album


def ecole_view(request):
    """Page 'L'École' - déjà existante."""
    valeurs = Valeur.objects.filter(actif=True)
    directeur = MembreDirection.objects.filter(
        actif=True,
        est_directeur=True
    ).first()
    autres_membres = MembreDirection.objects.filter(
        actif=True,
        est_directeur=False,
    )

    return render(request, 'pages/ecole.html', {
        'valeurs': valeurs,
        'directeur': directeur,
        'autres_membres': autres_membres,
    })


def galerie_view(request):
    """
    Liste de tous les albums photos publiés.

    OPTIMISATION : on annote chaque album avec le compte de ses photos
    pour éviter une requête supplémentaire par album dans le template.
    """
    from django.db.models import Count, Prefetch
    from .models import Photo

    # annotate(nb_photos=Count('photos')) ajoute un champ calculé
    # accessible via {{ album.nb_photos }} dans le template
    albums = Album.objects.filter(publie=True).annotate(
        nb_photos=Count('photos')
    ).prefetch_related(
        # On précharge la 1ère photo de chaque album pour la couverture fallback
        Prefetch(
            'photos',
            queryset=Photo.objects.order_by('ordre', 'created_at'),
        )
    )

    return render(request, 'pages/galerie.html', {
        'albums': albums,
    })


def album_detail_view(request, slug):
    """
    Détail d'un album : toutes les photos avec lightbox.
    """
    album = get_object_or_404(
        Album.objects.prefetch_related('photos'),
        slug=slug,
        publie=True,
    )

    photos = album.photos.all().order_by('ordre', 'created_at')

    # ============================================================
    # CONSTRUCTION DES DONNÉES JSON pour le lightbox JavaScript
    # ============================================================
    # On crée une liste de dictionnaires sérialisables pour le JS
    # Cela permet au lightbox de connaître toutes les photos sans
    # avoir à les recharger via AJAX.
    photos_data = [
        {
            'url': photo.image.url,
            'alt': photo.alt,
            'legende': photo.legende,
        }
        for photo in photos
    ]

    # Albums récents (sauf celui-ci)
    autres_albums = Album.objects.filter(
        publie=True
    ).exclude(pk=album.pk).order_by('-date_evenement')[:3]

    return render(request, 'pages/album_detail.html', {
        'album': album,
        'photos': photos,
        'photos_data': photos_data,  # ← NOUVEAU
        'autres_albums': autres_albums,
    })