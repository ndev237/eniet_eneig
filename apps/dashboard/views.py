from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .decorators import super_admin_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
from apps.blog.models import Article, Categorie
from .forms import ArticleForm, SiteSettingsForm, AlbumForm, MotDePasseForm, UtilisateurEditForm, UtilisateurCreationForm, MonMotDePasseForm, MonProfilForm
from apps.contacts.models import MessageContact
from django.core.mail import send_mail
from django.conf import settings
from apps.pages.models import SiteSettings, Album, Photo
import json
from django.contrib.auth import update_session_auth_hash

@login_required(login_url='dashboard:login')
def home(request):
    """
    Page d'accueil du dashboard : vue d'ensemble avec statistiques.

    @login_required : décorateur qui redirige vers /login/ si non connecté.
    L'argument login_url='dashboard:login' utilise notre URL custom au lieu
    de celle de Django par défaut (/accounts/login/).
    """

    # ============================================================
    # STATISTIQUES GLOBALES
    # ============================================================

    # Date il y a 30 jours pour les comparaisons
    il_y_a_30j = timezone.now() - timedelta(days=30)

    # Articles
    nb_articles_publies = Article.objects.publies().count()
    nb_articles_brouillons = Article.objects.filter(
        statut=Article.Statut.BROUILLON
    ).count()
    nb_articles_30j = Article.objects.filter(
        created_at__gte=il_y_a_30j
    ).count()

    # Messages
    nb_messages_non_lus = MessageContact.objects.filter(
        statut=MessageContact.StatutChoices.NON_LU
    ).count()
    nb_messages_30j = MessageContact.objects.filter(
        created_at__gte=il_y_a_30j
    ).count()

    # Albums
    nb_albums = Album.objects.filter(publie=True).count()

    # Vues totales des articles
    from django.db.models import Sum
    total_vues = Article.objects.publies().aggregate(
        total=Sum('nombre_vues')
    )['total'] or 0

    # ============================================================
    # DERNIERS ÉLÉMENTS
    # ============================================================
    derniers_articles = Article.objects.select_related('categorie').order_by(
        '-updated_at'
    )[:5]

    derniers_messages = MessageContact.objects.order_by('-created_at')[:5]

    # Articles les plus vus (top 5)
    articles_populaires = Article.objects.publies().order_by(
        '-nombre_vues'
    )[:5]

    return render(request, 'dashboard/home.html', {
        # Statistiques
        'nb_articles_publies': nb_articles_publies,
        'nb_articles_brouillons': nb_articles_brouillons,
        'nb_articles_30j': nb_articles_30j,
        'nb_messages_non_lus': nb_messages_non_lus,
        'nb_messages_30j': nb_messages_30j,
        'nb_albums': nb_albums,
        'total_vues': total_vues,

        # Listes
        'derniers_articles': derniers_articles,
        'derniers_messages': derniers_messages,
        'articles_populaires': articles_populaires,
    })


# ============================================================
# MODULE ARTICLES - CRUD
# ============================================================

@login_required(login_url='dashboard:login')
def articles_list(request):
    """
    Liste paginée des articles avec filtres et recherche.

    Filtres possibles :
    - statut : brouillon, publié, archivé
    - categorie : slug de la catégorie
    - q : recherche textuelle dans titre/résumé
    """
    # ============================================================
    # FILTRAGE
    # ============================================================
    # On part de TOUS les articles (pas seulement publiés)
    # car l'admin doit pouvoir voir les brouillons
    queryset = Article.objects.select_related('categorie', 'auteur').prefetch_related('tags')

    # Filtre par statut
    statut = request.GET.get('statut', '').strip()
    if statut and statut in [s[0] for s in Article.Statut.choices]:
        queryset = queryset.filter(statut=statut)

    # Filtre par catégorie
    categorie_slug = request.GET.get('categorie', '').strip()
    categorie_active = None
    if categorie_slug:
        try:
            categorie_active = Categorie.objects.get(slug=categorie_slug)
            queryset = queryset.filter(categorie=categorie_active)
        except Categorie.DoesNotExist:
            pass

    # Filtre par "à la une"
    a_la_une = request.GET.get('a_la_une') == '1'
    if a_la_une:
        queryset = queryset.filter(est_a_la_une=True)

    # Recherche
    recherche = request.GET.get('q', '').strip()
    if recherche:
        queryset = queryset.filter(
            Q(titre__icontains=recherche)
            | Q(resume__icontains=recherche)
            | Q(contenu__icontains=recherche)
        ).distinct()

    # ============================================================
    # TRI
    # ============================================================
    # Par défaut : du plus récent au plus ancien (déjà dans Meta.ordering)
    # Possibilité de surcharger via ?tri=vues, ?tri=titre
    tri = request.GET.get('tri', '-updated_at')
    tris_autorises = {
        '-updated_at': 'Modification récente',
        'updated_at': 'Modification ancienne',
        '-date_publication': 'Publication récente',
        '-nombre_vues': 'Plus vus',
        'titre': 'Titre A-Z',
        '-titre': 'Titre Z-A',
    }
    if tri in tris_autorises:
        queryset = queryset.order_by(tri)

    # ============================================================
    # PAGINATION
    # ============================================================
    paginator = Paginator(queryset, 20)  # 20 articles par page
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # ============================================================
    # STATS pour les badges de filtres
    # ============================================================
    stats = {
        'total': Article.objects.count(),
        'brouillons': Article.objects.filter(statut=Article.Statut.BROUILLON).count(),
        'publies': Article.objects.filter(statut=Article.Statut.PUBLIE).count(),
        'archives': Article.objects.filter(statut=Article.Statut.ARCHIVE).count(),
    }

    # Toutes les catégories pour le filtre
    categories = Categorie.objects.all()

    return render(request, 'dashboard/articles/list.html', {
        'page_obj': page_obj,
        'stats': stats,
        'categories': categories,
        'categorie_active': categorie_active,
        'statut_actif': statut,
        'recherche': recherche,
        'tri_actif': tri,
        'tris_autorises': tris_autorises,
        'a_la_une_actif': a_la_une,
    })


@login_required(login_url='dashboard:login')
def article_create(request):
    """
    Création d'un nouvel article.

    Workflow :
    - GET : affiche le formulaire vide
    - POST valide : crée l'article, message flash, redirection vers édition
    - POST invalide : ré-affiche avec erreurs
    """

    if request.method == 'POST':
        # request.FILES contient les fichiers uploadés (image_une)
        form = ArticleForm(request.POST, request.FILES)

        if form.is_valid():
            # commit=False : crée l'objet sans le sauvegarder en BDD
            # On peut alors le modifier avant le save()
            article = form.save(commit=False)

            # Assigne l'auteur à l'utilisateur connecté
            article.auteur = request.user

            # Sauvegarde en BDD
            article.save()

            # save_m2m() : sauvegarde des relations ManyToMany (tags)
            # Obligatoire APRÈS save() quand on a fait commit=False
            form.save_m2m()

            messages.success(
                request,
                f"✓ L'article « {article.titre} » a été créé avec succès."
            )

            # Redirige vers la page d'édition pour continuer à travailler
            return redirect('dashboard:article_update', pk=article.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ArticleForm()

    return render(request, 'dashboard/articles/form.html', {
        'form': form,
        'mode': 'create',
        'page_title': 'Nouvel article',
    })


@login_required(login_url='dashboard:login')
def article_update(request, pk):
    """
    Modification d'un article existant.

    pk = primary key (id de l'article)
    On utilise pk dans l'URL plutôt que slug pour :
    - Pas dépendre du slug (qui peut changer)
    - URL plus courte
    - Identifier de manière unique et stable
    """

    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        # instance=article : pré-remplit le formulaire avec l'article existant
        # Sans cela, le formulaire créerait un NOUVEL article au lieu de modifier
        form = ArticleForm(request.POST, request.FILES, instance=article)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"✓ L'article « {article.titre} » a été mis à jour."
            )

            # Si l'utilisateur a cliqué "Enregistrer et continuer", on reste sur la page
            # Sinon, on retourne à la liste
            if 'save_and_continue' in request.POST:
                return redirect('dashboard:article_update', pk=article.pk)
            return redirect('dashboard:articles_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ArticleForm(instance=article)

    return render(request, 'dashboard/articles/form.html', {
        'form': form,
        'article': article,
        'mode': 'update',
        'page_title': f'Modifier : {article.titre}',
    })


@login_required(login_url='dashboard:login')
def article_delete(request, pk):
    """
    Suppression d'un article avec confirmation.

    Pattern : on affiche d'abord une page de confirmation (GET),
    puis on supprime uniquement sur POST.

    C'est plus sûr que de supprimer directement avec un lien GET
    (un robot pourrait suivre le lien et tout supprimer).
    """

    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        titre = article.titre  # Sauvegarde avant suppression pour le message
        article.delete()

        messages.success(
            request,
            f"✓ L'article « {titre} » a été supprimé définitivement."
        )
        return redirect('dashboard:articles_list')

    return render(request, 'dashboard/articles/delete_confirm.html', {
        'article': article,
    })


# ============================================================
# ACTIONS RAPIDES (AJAX-like, retournent JSON)
# ============================================================

@login_required(login_url='dashboard:login')
@require_POST  # Décorateur : accepte uniquement POST (sécurité)
def article_toggle_publication(request, pk):
    """
    Bascule rapide entre Brouillon ↔ Publié.
    Utilisé depuis la liste des articles via AJAX ou form POST.
    """

    article = get_object_or_404(Article, pk=pk)

    # Bascule du statut
    if article.statut == Article.Statut.PUBLIE:
        article.statut = Article.Statut.BROUILLON
        message_action = "Article dépublié"
    else:
        article.statut = Article.Statut.PUBLIE
        message_action = "Article publié"

    article.save(update_fields=['statut'])  # Optimisation : ne sauve QUE ce champ

    messages.success(request, f"✓ {message_action} : « {article.titre} »")

    # Redirige vers la page d'où vient la requête
    # request.META.get('HTTP_REFERER') récupère l'URL précédente
    next_url = request.META.get('HTTP_REFERER', reverse('dashboard:articles_list'))
    return redirect(next_url)


@login_required(login_url='dashboard:login')
@require_POST
def article_toggle_une(request, pk):
    """
    Bascule rapide "À la une" on/off.
    """

    article = get_object_or_404(Article, pk=pk)
    article.est_a_la_une = not article.est_a_la_une
    article.save(update_fields=['est_a_la_une'])

    if article.est_a_la_une:
        messages.success(request, f"⭐ « {article.titre} » est maintenant à la une.")
    else:
        messages.info(request, f"« {article.titre} » n'est plus à la une.")

    next_url = request.META.get('HTTP_REFERER', reverse('dashboard:articles_list'))
    return redirect(next_url)


# ============================================================
# UPLOAD D'IMAGE DEPUIS TINYMCE
# ============================================================

@login_required(login_url='dashboard:login')
@require_POST
def tinymce_upload_image(request):
    """
    Endpoint utilisé par TinyMCE pour uploader une image dans le contenu.

    Quand l'utilisateur clique sur le bouton "Insérer image" de TinyMCE
    et choisit un fichier, TinyMCE envoie le fichier ici. On le sauvegarde
    et on retourne l'URL pour que TinyMCE puisse l'insérer.
    """


    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'Aucun fichier'}, status=400)

    # Vérification du type de fichier
    if not file.content_type.startswith('image/'):
        return JsonResponse({'error': 'Type de fichier non autorisé'}, status=400)

    # Chemin avec date pour éviter les collisions de noms
    date_path = datetime.now().strftime('%Y/%m')
    filename = f'blog/contenu/{date_path}/{file.name}'

    # Sauvegarde via le storage Django (gère automatiquement les doublons)
    saved_path = default_storage.save(filename, ContentFile(file.read()))
    file_url = default_storage.url(saved_path)

    return JsonResponse({'location': file_url})


# ============================================================
# MODULE MESSAGES - Boîte de réception
# ============================================================

@login_required(login_url='dashboard:login')
def messages_list(request):
    """
    Liste des messages reçus via le formulaire de contact.

    Filtres :
    - statut : non_lu, lu, traite
    - sujet : info, admission, formation, partenariat, autre
    - q : recherche dans nom, email, message
    """

    queryset = MessageContact.objects.all()

    # ============================================================
    # FILTRAGE PAR STATUT
    # ============================================================
    statut = request.GET.get('statut', '').strip()
    if statut and statut in [s[0] for s in MessageContact.StatutChoices.choices]:
        queryset = queryset.filter(statut=statut)

    # ============================================================
    # FILTRAGE PAR SUJET
    # ============================================================
    sujet = request.GET.get('sujet', '').strip()
    if sujet and sujet in [s[0] for s in MessageContact.SujetChoices.choices]:
        queryset = queryset.filter(sujet=sujet)

    # ============================================================
    # RECHERCHE
    # ============================================================
    recherche = request.GET.get('q', '').strip()
    if recherche:
        queryset = queryset.filter(
            Q(nom__icontains=recherche)
            | Q(email__icontains=recherche)
            | Q(message__icontains=recherche)
        )

    # ============================================================
    # PAGINATION
    # ============================================================
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # ============================================================
    # STATISTIQUES pour les onglets
    # ============================================================
    stats = {
        'total': MessageContact.objects.count(),
        'non_lus': MessageContact.objects.filter(
            statut=MessageContact.StatutChoices.NON_LU
        ).count(),
        'lus': MessageContact.objects.filter(
            statut=MessageContact.StatutChoices.LU
        ).count(),
        'traites': MessageContact.objects.filter(
            statut=MessageContact.StatutChoices.TRAITE
        ).count(),
    }

    return render(request, 'dashboard/messages/list.html', {
        'page_obj': page_obj,
        'stats': stats,
        'statut_actif': statut,
        'sujet_actif': sujet,
        'recherche': recherche,
        'sujets': MessageContact.SujetChoices.choices,
    })


@login_required(login_url='dashboard:login')
def message_detail(request, pk):
    """
    Détail d'un message + zone de réponse + note interne.

    COMPORTEMENT AUTOMATIQUE :
    Quand on ouvre un message NON LU, il passe automatiquement
    en statut LU. C'est le comportement attendu d'une boîte mail.
    """

    message = get_object_or_404(MessageContact, pk=pk)

    # ============================================================
    # MARQUER COMME LU AUTOMATIQUEMENT
    # ============================================================
    # Si le message est non lu, on le passe en "lu" dès l'ouverture
    # update_fields : on ne touche QUE le champ statut (optimisation)
    if message.statut == MessageContact.StatutChoices.NON_LU:
        message.statut = MessageContact.StatutChoices.LU
        message.save(update_fields=['statut', 'updated_at'])

    # ============================================================
    # MESSAGES PRÉCÉDENT/SUIVANT pour navigation
    # ============================================================
    # Permet de naviguer entre les messages sans revenir à la liste
    # On trie par date décroissante (comme dans la liste)
    message_precedent = MessageContact.objects.filter(
        created_at__gt=message.created_at
    ).order_by('created_at').first()

    message_suivant = MessageContact.objects.filter(
        created_at__lt=message.created_at
    ).order_by('-created_at').first()

    return render(request, 'dashboard/messages/detail.html', {
        'message': message,
        'message_precedent': message_precedent,
        'message_suivant': message_suivant,
    })


@login_required(login_url='dashboard:login')
@require_POST
def message_repondre(request, pk):
    """
    Envoie une réponse par email à l'expéditeur du message.

    Workflow :
    1. Récupère le texte de la réponse depuis le formulaire
    2. Envoie l'email à l'adresse de l'expéditeur
    3. Marque le message comme "traité"
    4. Enregistre la réponse dans la note interne (historique)
    """

    message = get_object_or_404(MessageContact, pk=pk)

    reponse_texte = request.POST.get('reponse', '').strip()

    # Validation : la réponse ne doit pas être vide
    if not reponse_texte:
        messages.error(request, "Le texte de la réponse ne peut pas être vide.")
        return redirect('dashboard:message_detail', pk=pk)

    # ============================================================
    # ENVOI DE L'EMAIL
    # ============================================================
    sujet_email = f"Réponse à votre message — ENIET / ENIEG"

    corps_email = f"""Bonjour {message.nom},

Suite à votre message concernant « {message.get_sujet_display()} », voici notre réponse :

{reponse_texte}

---
Cordialement,
L'équipe de l'ENIET / ENIEG
{settings.CONTACT_EMAIL}

---
Pour rappel, votre message initial était :
« {message.message} »
"""

    try:
        send_mail(
            subject=sujet_email,
            message=corps_email,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[message.email],
            fail_silently=False,
        )

        # ============================================================
        # MARQUER COMME TRAITÉ + HISTORISER LA RÉPONSE
        # ============================================================
        message.statut = MessageContact.StatutChoices.TRAITE

        # On ajoute la réponse à la note interne pour garder une trace
        horodatage = timezone.now().strftime('%d/%m/%Y à %H:%M')
        nouvelle_note = f"[Réponse envoyée le {horodatage} par {request.user.username}]\n{reponse_texte}"

        if message.note_interne:
            # On préserve les notes existantes
            message.note_interne = f"{nouvelle_note}\n\n---\n\n{message.note_interne}"
        else:
            message.note_interne = nouvelle_note

        message.save(update_fields=['statut', 'note_interne', 'updated_at'])

        messages.success(
            request,
            f"✓ Réponse envoyée à {message.email} et message marqué comme traité."
        )

    except Exception as e:
        # En cas d'échec d'envoi (SMTP non configuré, etc.)
        # En dev avec EMAIL_BACKEND=console, ça affiche dans le terminal
        messages.error(
            request,
            f"L'envoi a échoué : {e}. Vérifiez la configuration email."
        )

    return redirect('dashboard:message_detail', pk=pk)


@login_required(login_url='dashboard:login')
@require_POST
def message_note(request, pk):
    """
    Enregistre/modifie la note interne d'un message.
    La note interne n'est jamais visible par l'expéditeur.
    """

    message = get_object_or_404(MessageContact, pk=pk)

    note = request.POST.get('note_interne', '').strip()
    message.note_interne = note
    message.save(update_fields=['note_interne', 'updated_at'])

    messages.success(request, "✓ Note interne enregistrée.")
    return redirect('dashboard:message_detail', pk=pk)


@login_required(login_url='dashboard:login')
@require_POST
def message_changer_statut(request, pk):
    """
    Change le statut d'un message (non_lu, lu, traité).
    Utilisé pour les actions rapides depuis la liste ou le détail.
    """

    message = get_object_or_404(MessageContact, pk=pk)

    nouveau_statut = request.POST.get('statut', '').strip()

    # Validation : le statut doit être valide
    statuts_valides = [s[0] for s in MessageContact.StatutChoices.choices]
    if nouveau_statut in statuts_valides:
        message.statut = nouveau_statut
        message.save(update_fields=['statut', 'updated_at'])

        libelle = message.get_statut_display()
        messages.success(request, f"✓ Message marqué comme « {libelle} ».")

    next_url = request.META.get('HTTP_REFERER', reverse('dashboard:messages_list'))
    return redirect(next_url)


@login_required(login_url='dashboard:login')
def message_delete(request, pk):
    """
    Suppression d'un message avec confirmation.
    """

    message = get_object_or_404(MessageContact, pk=pk)

    if request.method == 'POST':
        nom = message.nom
        message.delete()
        messages.success(request, f"✓ Le message de {nom} a été supprimé.")
        return redirect('dashboard:messages_list')

    return render(request, 'dashboard/messages/delete_confirm.html', {
        'message': message,
    })


# ============================================================
# MODULE PARAMÈTRES DU SITE
# ============================================================

@login_required(login_url='dashboard:login')
def parametres(request):
    """
    Édition des paramètres globaux du site (singleton SiteSettings).

    Différence avec un CRUD classique :
    - Pas de liste : il n'y a qu'un seul objet de paramètres
    - Pas de création : l'objet existe déjà (créé via migration)
    - Pas de suppression : on ne supprime jamais les paramètres
    - Uniquement de l'édition

    On charge l'instance unique via SiteSettings.load() (méthode définie
    dans le modèle qui fait get_or_create avec pk=1).
    """

    # Charge l'instance unique (la crée si elle n'existe pas)
    settings_obj = SiteSettings.load()

    if request.method == 'POST':
        # instance=settings_obj : on modifie l'objet existant
        form = SiteSettingsForm(request.POST, instance=settings_obj)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "✓ Les paramètres du site ont été enregistrés avec succès."
            )
            # PRG : on redirige vers la même page pour éviter le re-POST au F5
            return redirect('dashboard:parametres')
        else:
            messages.error(
                request,
                "Certains champs contiennent des erreurs. Veuillez vérifier."
            )
    else:
        form = SiteSettingsForm(instance=settings_obj)

    return render(request, 'dashboard/parametres/index.html', {
        'form': form,
        'settings_obj': settings_obj,
    })


# ============================================================
# MODULE MÉDIAS / GALERIE
# ============================================================

@login_required(login_url='dashboard:login')
def medias_list(request):
    """
    Liste de tous les albums (grille avec couvertures).
    """

    # Annotate pour compter les photos de chaque album (évite N+1)
    albums = Album.objects.annotate(
        nb_photos=Count('photos')
    ).order_by('-date_evenement')

    # Stats
    stats = {
        'total': albums.count(),
        'publies': Album.objects.filter(publie=True).count(),
        'brouillons': Album.objects.filter(publie=False).count(),
    }

    return render(request, 'dashboard/medias/list.html', {
        'albums': albums,
        'stats': stats,
    })


@login_required(login_url='dashboard:login')
def album_create(request):
    """
    Création d'un nouvel album.
    Après création, on redirige vers l'édition pour ajouter les photos.
    """

    if request.method == 'POST':
        form = AlbumForm(request.POST, request.FILES)
        if form.is_valid():
            album = form.save()
            messages.success(
                request,
                f"✓ L'album « {album.titre} » a été créé. Ajoutez maintenant des photos."
            )
            return redirect('dashboard:album_edit', pk=album.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = AlbumForm()

    return render(request, 'dashboard/medias/album_form.html', {
        'form': form,
        'mode': 'create',
        'page_title': 'Nouvel album',
    })


@login_required(login_url='dashboard:login')
def album_edit(request, pk):
    """
    Édition d'un album : infos + gestion des photos.

    Cette vue gère uniquement le formulaire d'infos de l'album.
    Les photos sont gérées par les endpoints AJAX séparés
    (upload, suppression, réorganisation).
    """
    album = get_object_or_404(Album, pk=pk)

    if request.method == 'POST':
        form = AlbumForm(request.POST, request.FILES, instance=album)
        if form.is_valid():
            form.save()
            messages.success(request, "✓ Les informations de l'album ont été mises à jour.")
            return redirect('dashboard:album_edit', pk=album.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = AlbumForm(instance=album)

    # Photos de l'album, triées par ordre
    photos = album.photos.all().order_by('ordre', 'created_at')

    return render(request, 'dashboard/medias/album_form.html', {
        'form': form,
        'album': album,
        'photos': photos,
        'mode': 'edit',
        'page_title': f'Modifier : {album.titre}',
    })


@login_required(login_url='dashboard:login')
def album_delete(request, pk):
    """
    Suppression d'un album (et de toutes ses photos en cascade).
    """

    album = get_object_or_404(Album, pk=pk)

    if request.method == 'POST':
        titre = album.titre
        # La suppression en cascade des photos est automatique
        # grâce à on_delete=CASCADE défini sur le modèle Photo
        album.delete()
        messages.success(request, f"✓ L'album « {titre} » et ses photos ont été supprimés.")
        return redirect('dashboard:medias_list')

    return render(request, 'dashboard/medias/delete_confirm.html', {
        'album': album,
    })


# ============================================================
# ENDPOINTS AJAX pour la gestion des photos
# ============================================================

@login_required(login_url='dashboard:login')
@require_POST
def photos_upload(request, album_pk):
    """
    Upload multiple de photos dans un album (via AJAX).

    Le JavaScript envoie un ou plusieurs fichiers via FormData.
    On les sauvegarde et on retourne les infos en JSON pour que
    le front puisse afficher les nouvelles vignettes sans recharger.

    request.FILES.getlist('photos') : récupère TOUS les fichiers
    envoyés sous le nom 'photos' (upload multiple).
    """

    album = get_object_or_404(Album, pk=album_pk)

    fichiers = request.FILES.getlist('photos')

    if not fichiers:
        return JsonResponse({'error': 'Aucun fichier reçu'}, status=400)

    # On détermine l'ordre de départ (après les photos existantes)
    from django.db.models import Max
    dernier_ordre = album.photos.aggregate(
        max_ordre=Max('ordre')
    )['max_ordre'] or 0

    photos_creees = []

    for index, fichier in enumerate(fichiers):
        # Validation : doit être une image
        if not fichier.content_type.startswith('image/'):
            continue  # On ignore les fichiers non-image

        # Création de la photo
        photo = Photo.objects.create(
            album=album,
            image=fichier,
            alt=f"{album.titre} - photo {dernier_ordre + index + 1}",
            ordre=dernier_ordre + index + 1,
        )

        # On prépare les données à renvoyer au front
        photos_creees.append({
            'id': photo.pk,
            'url': photo.image.url,
            'alt': photo.alt,
            'ordre': photo.ordre,
        })

    return JsonResponse({
        'success': True,
        'photos': photos_creees,
        'message': f"{len(photos_creees)} photo(s) ajoutée(s).",
    })


@login_required(login_url='dashboard:login')
@require_POST
def photo_delete(request, pk):
    """
    Suppression d'une photo individuelle (via AJAX).
    Retourne JSON pour que le front retire la vignette sans recharger.
    """

    photo = get_object_or_404(Photo, pk=pk)
    photo_id = photo.pk

    # Supprime le fichier physique ET l'entrée en BDD
    photo.image.delete(save=False)  # Supprime le fichier du disque
    photo.delete()  # Supprime l'entrée BDD

    return JsonResponse({
        'success': True,
        'id': photo_id,
    })


@login_required(login_url='dashboard:login')
@require_POST
def photo_update_legende(request, pk):
    """
    Met à jour la légende et le texte alt d'une photo (via AJAX).
    """

    photo = get_object_or_404(Photo, pk=pk)

    # Les données arrivent en JSON depuis le front
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données invalides'}, status=400)

    photo.legende = data.get('legende', '').strip()
    alt = data.get('alt', '').strip()
    if alt:  # alt est obligatoire, on ne le vide pas
        photo.alt = alt
    photo.save(update_fields=['legende', 'alt', 'updated_at'])

    return JsonResponse({'success': True})


@login_required(login_url='dashboard:login')
@require_POST
def photos_reorder(request, album_pk):
    """
    Réorganise les photos d'un album (via drag & drop AJAX).

    Le front envoie la nouvelle liste des IDs dans l'ordre souhaité.
    On met à jour le champ 'ordre' de chaque photo.
    """

    album = get_object_or_404(Album, pk=album_pk)

    try:
        data = json.loads(request.body)
        ordre_ids = data.get('ordre', [])  # Liste d'IDs dans le nouvel ordre
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données invalides'}, status=400)

    # Mise à jour de l'ordre de chaque photo
    # enumerate démarre à 0, donc photo en position 0 = ordre 1
    for nouvel_ordre, photo_id in enumerate(ordre_ids, start=1):
        Photo.objects.filter(
            pk=photo_id,
            album=album,  # Sécurité : on vérifie que la photo appartient à l'album
        ).update(ordre=nouvel_ordre)

    return JsonResponse({'success': True})


# ============================================================
# MODULE UTILISATEURS (super-admin uniquement)
# ============================================================


@login_required(login_url='dashboard:login')
@super_admin_required
def utilisateurs_list(request):
    """
    Liste des utilisateurs du dashboard.
    Accessible uniquement aux super-admins (via le décorateur).
    """

    # select_related('profil') : charge le profil en une seule requête (évite N+1)
    utilisateurs = User.objects.select_related('profil').order_by('-date_joined')

    # Recherche
    recherche = request.GET.get('q', '').strip()
    if recherche:
        utilisateurs = utilisateurs.filter(
            Q(username__icontains=recherche)
            | Q(first_name__icontains=recherche)
            | Q(last_name__icontains=recherche)
            | Q(email__icontains=recherche)
        )

    # Stats par rôle
    from .models import Profil
    stats = {
        'total': User.objects.count(),
        'super_admins': Profil.objects.filter(role=Profil.Role.SUPER_ADMIN).count(),
        'editeurs': Profil.objects.filter(role=Profil.Role.EDITEUR).count(),
        'actifs': User.objects.filter(is_active=True).count(),
    }

    return render(request, 'dashboard/utilisateurs/list.html', {
        'utilisateurs': utilisateurs,
        'stats': stats,
        'recherche': recherche,
    })


@login_required(login_url='dashboard:login')
@super_admin_required
def utilisateur_create(request):
    """
    Création d'un nouvel utilisateur.
    """

    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"✓ Le compte de {user.get_full_name()} a été créé avec succès."
            )
            return redirect('dashboard:utilisateurs_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = UtilisateurCreationForm()

    return render(request, 'dashboard/utilisateurs/form.html', {
        'form': form,
        'mode': 'create',
        'page_title': 'Nouvel utilisateur',
    })


@login_required(login_url='dashboard:login')
@super_admin_required
def utilisateur_edit(request, pk):
    """
    Édition d'un utilisateur existant (infos + rôle).
    """

    utilisateur = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UtilisateurEditForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"✓ Le compte de {utilisateur.get_full_name() or utilisateur.username} a été mis à jour."
            )
            return redirect('dashboard:utilisateurs_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = UtilisateurEditForm(instance=utilisateur)

    return render(request, 'dashboard/utilisateurs/form.html', {
        'form': form,
        'utilisateur': utilisateur,
        'mode': 'edit',
        'page_title': f'Modifier : {utilisateur.username}',
    })


@login_required(login_url='dashboard:login')
@super_admin_required
def utilisateur_password(request, pk):
    """
    Changement du mot de passe d'un utilisateur.
    """

    utilisateur = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # SetPasswordForm prend l'utilisateur en premier argument
        form = MotDePasseForm(utilisateur, request.POST)
        if form.is_valid():
            form.save()  # Hash et sauvegarde le nouveau mot de passe
            messages.success(
                request,
                f"✓ Le mot de passe de {utilisateur.username} a été modifié."
            )
            return redirect('dashboard:utilisateurs_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = MotDePasseForm(utilisateur)

    return render(request, 'dashboard/utilisateurs/password.html', {
        'form': form,
        'utilisateur': utilisateur,
    })


@login_required(login_url='dashboard:login')
@super_admin_required
@require_POST
def utilisateur_toggle_actif(request, pk):
    """
    Active / désactive un compte utilisateur.

    Un compte désactivé ne peut plus se connecter, mais ses données
    (articles, etc.) restent intactes. C'est mieux que la suppression.

    SÉCURITÉ : on empêche de se désactiver soi-même (sinon on se bloque).
    """

    utilisateur = get_object_or_404(User, pk=pk)

    # Empêche l'auto-désactivation
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('dashboard:utilisateurs_list')

    # Bascule l'état actif
    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save(update_fields=['is_active'])

    if utilisateur.is_active:
        messages.success(request, f"✓ Le compte de {utilisateur.username} a été réactivé.")
    else:
        messages.info(request, f"Le compte de {utilisateur.username} a été désactivé.")

    return redirect('dashboard:utilisateurs_list')


@login_required(login_url='dashboard:login')
@super_admin_required
def utilisateur_delete(request, pk):
    """
    Suppression d'un utilisateur avec confirmation.

    SÉCURITÉ : on empêche de se supprimer soi-même.
    Note : grâce à on_delete=SET_NULL sur Article.auteur,
    les articles de l'utilisateur supprimé restent (auteur = NULL).
    """

    utilisateur = get_object_or_404(User, pk=pk)

    # Empêche l'auto-suppression
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('dashboard:utilisateurs_list')

    if request.method == 'POST':
        username = utilisateur.username
        utilisateur.delete()
        messages.success(request, f"✓ Le compte de {username} a été supprimé.")
        return redirect('dashboard:utilisateurs_list')

    return render(request, 'dashboard/utilisateurs/delete_confirm.html', {
        'utilisateur': utilisateur,
    })


# ============================================================
# PROFIL PERSONNEL (accessible par tous)
# ============================================================

@login_required(login_url='dashboard:login')
def mon_profil(request):
    """
    Édition de son propre profil.
    Pas de @super_admin_required : tout le monde gère son profil.
    """

    profil = request.user.profil

    if request.method == 'POST':
        form = MonProfilForm(request.POST, request.FILES, instance=profil)
        if form.is_valid():
            form.save()
            messages.success(request, "✓ Votre profil a été mis à jour.")
            return redirect('dashboard:mon_profil')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = MonProfilForm(instance=profil)

    return render(request, 'dashboard/profil/index.html', {
        'form': form,
    })


@login_required(login_url='dashboard:login')
def mon_mot_de_passe(request):
    """
    Changement de son propre mot de passe.

    IMPORTANT : update_session_auth_hash évite la déconnexion
    après changement de mot de passe. Sans ça, Django invaliderait
    la session et l'utilisateur serait éjecté.
    """

    if request.method == 'POST':
        form = MonMotDePasseForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Maintient la session active après le changement
            update_session_auth_hash(request, user)
            messages.success(request, "✓ Votre mot de passe a été changé avec succès.")
            return redirect('dashboard:mon_profil')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = MonMotDePasseForm(request.user)

    return render(request, 'dashboard/profil/mot_de_passe.html', {
        'form': form,
    })