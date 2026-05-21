"""
Crée les catégories, tags et articles de démonstration.
"""

from datetime import timedelta
from django.db import migrations
from django.utils import timezone


def creer_donnees_initiales(apps, schema_editor):
    """Crée catégories, tags et 3 articles de démonstration."""
    Categorie = apps.get_model('blog', 'Categorie')
    Tag = apps.get_model('blog', 'Tag')
    Article = apps.get_model('blog', 'Article')
    User = apps.get_model('auth', 'User')

    # ============================================================
    # CATÉGORIES
    # ============================================================
    categories_data = [
        {
            'nom': 'Événement',
            'slug': 'evenement',
            'description': 'Cérémonies, journées portes ouvertes et grands moments de l\'établissement.',
            'couleur': 'accent',
            'ordre': 1,
        },
        {
            'nom': 'Communiqué',
            'slug': 'communique',
            'description': 'Annonces officielles, dates de concours et informations importantes.',
            'couleur': 'primary',
            'ordre': 2,
        },
        {
            'nom': 'Vie scolaire',
            'slug': 'vie-scolaire',
            'description': 'Ateliers, sorties pédagogiques et activités du quotidien.',
            'couleur': 'blue',
            'ordre': 3,
        },
        {
            'nom': 'Résultats',
            'slug': 'resultats',
            'description': 'Résultats des concours et des examens.',
            'couleur': 'purple',
            'ordre': 4,
        },
    ]

    categories = {}
    for cat_data in categories_data:
        cat, _ = Categorie.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data,
        )
        categories[cat.slug] = cat

    # ============================================================
    # TAGS
    # ============================================================
    tags_noms = [
        'diplômes', 'promotion 2025', 'MINESEC', 'cérémonie',
        'concours', 'inscriptions', 'ENIET', 'ENIEG',
        'atelier', 'électricité', 'partenariat', 'industrie',
        'bâtiment', 'pédagogie', 'CAPIEMP', 'CAPIET',
    ]

    tags = {}
    for tag_nom in tags_noms:
        from django.utils.text import slugify
        tag, _ = Tag.objects.get_or_create(
            nom=tag_nom,
            defaults={'slug': slugify(tag_nom)},
        )
        tags[tag_nom] = tag

    # ============================================================
    # AUTEUR PAR DÉFAUT
    # ============================================================
    # On essaie de récupérer le superuser, sinon on met None
    auteur = User.objects.filter(is_superuser=True).first()

    # ============================================================
    # ARTICLES DE DÉMO
    # ============================================================
    # Note : pas d'image_une car on ne peut pas créer de fichiers
    # depuis une migration. L'admin uploadera les vraies images.

    articles_data = [
        {
            'titre': 'Cérémonie de remise des diplômes : promotion 2025',
            'slug': 'ceremonie-remise-diplomes-promotion-2025',
            'resume': 'Notre établissement a célébré la 8ᵉ promotion d\'instituteurs diplômés lors d\'une cérémonie en présence du Délégué Régional du MINESEC.',
            'contenu': '''<p>Le 15 mai 2026, l\'ENIET/ENIEG a célébré dans une ambiance solennelle la remise des diplômes à la 8ᵉ promotion d\'instituteurs formés au sein de notre établissement.</p>

<p>Cette cérémonie, qui s\'est déroulée en présence de Monsieur le Délégué Régional des Enseignements Secondaires du Littoral, a vu la consécration de plus de 80 nouveaux instituteurs titulaires des Certificats d\'Aptitude Pédagogique CAPIEMP et CAPIET.</p>

<h2>Une promotion d\'excellence</h2>

<p>Avec un taux de réussite global de 94%, cette promotion confirme la qualité de la formation dispensée à l\'ENIET/ENIEG. Les majors de promotion ont été honorés par des prix spéciaux remis par les autorités présentes.</p>

<p>Dans son allocution, le directeur de l\'établissement a rappelé l\'importance du rôle des instituteurs dans la construction de l\'avenir éducatif du Cameroun, et a invité les nouveaux diplômés à porter haut les valeurs d\'excellence professionnelle inculquées durant leur formation.</p>

<h2>Perspectives</h2>

<p>Tous les diplômés ont déjà reçu leurs premières propositions d\'affectation et rejoindront prochainement les écoles publiques et privées du pays pour exercer leur noble mission.</p>''',
            'image_une_alt': 'Cérémonie de remise des diplômes promotion 2025',
            'categorie_slug': 'evenement',
            'tags_noms': ['diplômes', 'promotion 2025', 'MINESEC', 'cérémonie'],
            'est_a_la_une': True,
            'jours_avant_maintenant': 5,
        },
        {
            'titre': 'Ouverture des inscriptions au concours 2025-2026',
            'slug': 'ouverture-inscriptions-concours-2025-2026',
            'resume': 'Les inscriptions au concours d\'entrée pour l\'année scolaire 2025-2026 sont officiellement ouvertes. Découvrez les modalités.',
            'contenu': '''<p>Nous avons le plaisir d\'annoncer l\'ouverture officielle des inscriptions au concours d\'entrée à l\'ENIET et à l\'ENIEG pour l\'année scolaire 2025-2026.</p>

<h2>Conditions d\'admission</h2>

<p>Le concours est ouvert :</p>
<ul>
<li><strong>Pour l\'ENIEG (CAPIEMP)</strong> : aux titulaires du Baccalauréat de l\'enseignement général.</li>
<li><strong>Pour l\'ENIET (CAPIET)</strong> : aux titulaires de BT, PBT, BP ou Baccalauréat de l\'enseignement technique industriel et commercial.</li>
</ul>

<h2>Frais et calendrier</h2>

<p>Les frais de concours s\'élèvent à <strong>12 000 FCFA non remboursables</strong>. Le dépôt des dossiers se fait à l\'établissement situé à Yassa, à 100 mètres avant la station Tradex.</p>

<h2>Constituer son dossier</h2>

<p>Consultez notre page <a href="/fr/formations/admission/">Admission</a> pour la liste complète des documents à fournir et toute information complémentaire.</p>''',
            'image_une_alt': 'Affiche d\'ouverture des inscriptions au concours',
            'categorie_slug': 'communique',
            'tags_noms': ['concours', 'inscriptions', 'ENIET', 'ENIEG'],
            'est_a_la_une': True,
            'jours_avant_maintenant': 15,
        },
        {
            'titre': 'Atelier pratique de la filière Électricité avec un partenaire industriel',
            'slug': 'atelier-pratique-electricite-partenaire-industriel',
            'resume': 'Les élèves-maîtres de la filière Électricité ont bénéficié d\'un atelier pratique animé par les experts d\'une entreprise industrielle locale.',
            'contenu': '''<p>Dans le cadre du renforcement de la formation pratique de nos élèves-maîtres, la filière Électricité de l\'ENIET a accueilli ce mois-ci un atelier exceptionnel animé par les experts d\'une grande entreprise industrielle locale.</p>

<h2>Un partenariat enrichissant</h2>

<p>Pendant deux journées intensives, nos élèves-maîtres ont pu manipuler des équipements professionnels modernes et bénéficier des conseils d\'ingénieurs expérimentés. Les thématiques abordées comprenaient :</p>

<ul>
<li>Sécurité électrique en milieu industriel</li>
<li>Installations basse tension complexes</li>
<li>Maintenance préventive et diagnostic de pannes</li>
<li>Méthodes pédagogiques pour transmettre ces savoir-faire</li>
</ul>

<h2>L\'avis des participants</h2>

<p>"C\'est une opportunité incroyable de voir comment se passent les choses en entreprise. Cela va enrichir notre future pratique pédagogique", témoigne un élève-maître.</p>

<p>Ces ateliers s\'inscrivent dans notre démarche d\'ouverture vers le monde professionnel pour assurer une formation pratique de qualité, en phase avec les réalités du terrain camerounais.</p>''',
            'image_une_alt': 'Atelier pratique d\'électricité',
            'categorie_slug': 'vie-scolaire',
            'tags_noms': ['atelier', 'électricité', 'partenariat', 'industrie'],
            'est_a_la_une': False,
            'jours_avant_maintenant': 25,
        },
    ]

    now = timezone.now()

    for art_data in articles_data:
        # Extraire les données spécifiques avant get_or_create
        categorie_slug = art_data.pop('categorie_slug')
        tags_noms = art_data.pop('tags_noms')
        jours_avant = art_data.pop('jours_avant_maintenant')

        # Date de publication : maintenant - X jours
        date_pub = now - timedelta(days=jours_avant)

        # Création de l'article
        article, created = Article.objects.get_or_create(
            slug=art_data['slug'],
            defaults={
                **art_data,
                'categorie': categories[categorie_slug],
                'auteur': auteur,
                'statut': 'publie',
                'date_publication': date_pub,
            },
        )

        # Ajout des tags (ManyToMany : .set() pour remplacer, .add() pour ajouter)
        if created:
            tags_objs = [tags[nom] for nom in tags_noms]
            article.tags.set(tags_objs)


def supprimer_donnees_initiales(apps, schema_editor):
    """Rollback : supprime les données de démo."""
    Article = apps.get_model('blog', 'Article')
    Categorie = apps.get_model('blog', 'Categorie')
    Tag = apps.get_model('blog', 'Tag')

    Article.objects.all().delete()
    Categorie.objects.all().delete()
    Tag.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            creer_donnees_initiales,
            reverse_code=supprimer_donnees_initiales,
        ),
    ]
