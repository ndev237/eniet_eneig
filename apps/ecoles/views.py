from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch

from .models import Ecole, TranchePaiement, DocumentRequis, FAQ, Filiere


def admission_view(request):
    """
    Vue de la page Admission (déjà existante).
    """
    ecoles = Ecole.objects.filter(actif=True).prefetch_related(
        Prefetch(
            'tranches',
            queryset=TranchePaiement.objects.order_by('annee', 'numero_tranche'),
            to_attr='tranches_triees',
        )
    )
    documents = DocumentRequis.objects.all()
    faqs = FAQ.objects.filter(actif=True)

    return render(request, 'ecoles/admission.html', {
        'ecoles': ecoles,
        'documents': documents,
        'faqs': faqs,
    })


def formations_list_view(request):
    """
    Liste des formations : vue d'ensemble des écoles et filières.

    Page d'entrée vers le détail de chaque école.
    On précharge les filières pour éviter le problème N+1.
    """
    ecoles = Ecole.objects.filter(actif=True).prefetch_related(
        Prefetch(
            'filieres',
            queryset=Filiere.objects.filter(actif=True),
            to_attr='filieres_actives',
        )
    )

    return render(request, 'ecoles/formations_list.html', {
        'ecoles': ecoles,
    })


def ecole_detail_view(request, ecole_slug):
    """
    Détail d'une école (ENIEG ou ENIET).

    NOUVELLE NOTION : URL avec PARAMÈTRE

    L'URL /formations/enieg/ capture 'enieg' dans la variable ecole_slug.
    On utilise cette variable pour retrouver l'objet en BDD.

    get_object_or_404 :
    - Cherche l'objet selon les critères
    - S'il existe : retourne l'objet
    - S'il n'existe pas : retourne automatiquement une page 404

    C'est plus propre que :
        try:
            ecole = Ecole.objects.get(slug=ecole_slug)
        except Ecole.DoesNotExist:
            raise Http404
    """
    ecole = get_object_or_404(
        Ecole.objects.prefetch_related('filieres', 'tranches'),
        slug=ecole_slug,
        actif=True,
    )

    # Filières actives uniquement, triées
    filieres = ecole.filieres.filter(actif=True).order_by('ordre', 'nom')

    # Tranches triées
    tranches = ecole.tranches.order_by('annee', 'numero_tranche')

    return render(request, 'ecoles/ecole_detail.html', {
        'ecole': ecole,
        'filieres': filieres,
        'tranches': tranches,
    })


def filiere_detail_view(request, ecole_slug, filiere_slug):
    """
    Détail d'une filière spécifique.

    URL : /formations/eniet/electricite/

    On capture DEUX paramètres dans l'URL :
    - ecole_slug = 'eniet'
    - filiere_slug = 'electricite'

    On vérifie que la filière appartient bien à l'école pour éviter
    qu'un visiteur tape une URL incohérente comme /formations/enieg/couture/.
    """
    filiere = get_object_or_404(
        Filiere.objects.select_related('ecole'),  # ← optimisation : 1 seule requête au lieu de 2
        ecole__slug=ecole_slug,
        slug=filiere_slug,
        actif=True,
    )

    # Autres filières de la même école pour la section "Voir aussi"
    # .exclude(pk=filiere.pk) retire la filière courante
    autres_filieres = Filiere.objects.filter(
        ecole=filiere.ecole,
        actif=True,
    ).exclude(pk=filiere.pk).order_by('?')[:3]  # ← '?' = ordre aléatoire, limité à 3

    return render(request, 'ecoles/filiere_detail.html', {
        'filiere': filiere,
        'autres_filieres': autres_filieres,
    })