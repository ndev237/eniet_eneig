"""
Insère les 7 filières de l'ENIET d'après les arrêtés officiels.
"""

from django.db import migrations


def creer_filieres(apps, schema_editor):
    """Crée les 7 filières techniques de l'ENIET."""
    Ecole = apps.get_model('ecoles', 'Ecole')
    Filiere = apps.get_model('ecoles', 'Filiere')

    # Récupère ENIET - doit exister via la migration 0002
    try:
        eniet = Ecole.objects.get(sigle='ENIET')
    except Ecole.DoesNotExist:
        # Sécurité : si ENIET n'existe pas, on ne crée rien
        return

    # ============================================================
    # LES 7 FILIÈRES ENIET (extraites des PDF officiels)
    # ============================================================
    filieres_data = [
        {
            'nom': 'Électricité',
            'slug': 'electricite',
            'description_courte': 'Formation aux installations électriques, à la maintenance et à la pédagogie de la spécialité électrique.',
            'description_longue': 'La filière Électricité forme des instituteurs capables d\'enseigner les fondamentaux de l\'électrotechnique aux élèves de l\'enseignement technique. Les diplômés maîtrisent à la fois les compétences techniques (installations, maintenance, dépannage) et la pédagogie nécessaire pour transmettre efficacement ces savoirs.',
            'debouches': 'Instituteur d\'enseignement technique en électricité dans les lycées et collèges techniques publics et privés du Cameroun. Possibilité d\'évolution vers les fonctions d\'encadrement pédagogique.',
            'competences_acquises': 'Conception d\'installations électriques basse tension\nMaintenance préventive et corrective\nLecture et réalisation de schémas électriques\nMéthodes pédagogiques adaptées à l\'enseignement technique\nGestion d\'un atelier de formation',
            'matieres_principales': 'Électrotechnique générale\nÉlectricité industrielle\nMesures électriques\nSécurité électrique\nPédagogie générale et spécialisée\nDidactique de l\'électricité',
            'icone': 'bolt',
            'ordre': 1,
        },
        {
            'nom': 'Construction en Maçonnerie et Béton Armé',
            'slug': 'maconnerie-beton',
            'description_courte': 'Formation aux techniques de construction, structures porteuses et pédagogie du bâtiment.',
            'description_longue': 'La filière Construction prépare les futurs instituteurs à enseigner les métiers du bâtiment. Du gros œuvre aux finitions, en passant par les calculs de structure, les élèves-maîtres acquièrent une vision complète du secteur de la construction.',
            'debouches': 'Instituteur dans les lycées techniques du bâtiment. Encadrement de stagiaires sur les chantiers pédagogiques. Conseil technique en construction.',
            'competences_acquises': 'Lecture de plans architecturaux\nTechniques de maçonnerie traditionnelle et moderne\nCalcul de structures en béton armé\nGestion de chantier-école\nDidactique des métiers du bâtiment',
            'matieres_principales': 'Technologie de la maçonnerie\nRésistance des matériaux\nBéton armé\nDessin technique du bâtiment\nPédagogie professionnelle\nSécurité sur les chantiers',
            'icone': 'building',
            'ordre': 2,
        },
        {
            'nom': 'Couture (Flou)',
            'slug': 'couture',
            'description_courte': 'Techniques de couture flou, design textile et enseignement professionnel du vêtement.',
            'description_longue': 'La filière Couture forme des instituteurs spécialisés dans l\'enseignement des techniques de couture flou (vêtements féminins légers). Au-delà du savoir-faire technique, l\'accent est mis sur la créativité, le design et la transmission pédagogique de ces compétences.',
            'debouches': 'Instituteur dans les centres de formation professionnelle. Formateur en couture-mode. Création d\'un atelier de couture pédagogique.',
            'competences_acquises': 'Patronage et modélisme\nTechniques de couture flou\nChoix et travail des tissus\nDessin de mode\nGestion d\'un atelier pédagogique',
            'matieres_principales': 'Technologie de la couture\nDessin de mode\nPatronage\nHistoire du costume\nPédagogie générale\nDidactique de la couture',
            'icone': 'scissors',
            'ordre': 3,
        },
        {
            'nom': 'Économie Sociale et Familiale',
            'slug': 'economie-sociale-familiale',
            'description_courte': 'Sciences humaines appliquées à la vie domestique, sociale et familiale.',
            'description_longue': 'L\'ESF est une filière transversale qui forme des instituteurs capables d\'enseigner l\'art de la vie domestique : nutrition, gestion du foyer, hygiène, éducation familiale. Une formation à fort impact social pour accompagner les familles camerounaises.',
            'debouches': 'Instituteur en économie sociale et familiale dans l\'enseignement technique. Travailleur social en organisme communautaire. Animateur d\'ateliers familiaux.',
            'competences_acquises': 'Nutrition et diététique\nÉducation à la santé familiale\nGestion budgétaire du foyer\nAnimation de groupes\nPédagogie sociale',
            'matieres_principales': 'Nutrition et alimentation\nPuériculture et éducation familiale\nÉconomie domestique\nHygiène et santé\nPsychopédagogie\nDidactique de l\'ESF',
            'icone': 'home',
            'ordre': 4,
        },
        {
            'nom': 'Comptabilité et Gestion',
            'slug': 'comptabilite-gestion',
            'description_courte': 'Méthodes comptables, gestion d\'entreprise et didactique des sciences de gestion.',
            'description_longue': 'La filière Comptabilité et Gestion forme des instituteurs aptes à enseigner les bases de la comptabilité, de la gestion d\'entreprise et de la fiscalité. Une formation rigoureuse pour transmettre des compétences immédiatement valorisables dans le monde professionnel.',
            'debouches': 'Instituteur de comptabilité dans les lycées techniques commerciaux. Formateur en gestion pour les PME. Conseil en gestion administrative.',
            'competences_acquises': 'Comptabilité générale et analytique\nAnalyse financière\nGestion budgétaire\nDroit fiscal de base\nDidactique de la comptabilité',
            'matieres_principales': 'Comptabilité générale\nComptabilité des sociétés\nGestion budgétaire\nDroit commercial\nPédagogie\nDidactique des sciences de gestion',
            'icone': 'chart',
            'ordre': 5,
        },
        {
            'nom': 'Bureautique',
            'slug': 'bureautique',
            'description_courte': 'Outils numériques de bureau et formation pédagogique aux logiciels professionnels.',
            'description_longue': 'La filière Bureautique forme les instituteurs aux outils informatiques du monde professionnel : traitement de texte, tableurs, présentations, gestion de bases de données. Une formation moderne et essentielle pour préparer la jeunesse aux exigences du marché du travail numérique.',
            'debouches': 'Instituteur en bureautique dans les lycées techniques. Formateur en informatique de bureau. Animateur de centres de formation continue.',
            'competences_acquises': 'Maîtrise des suites bureautiques (Word, Excel, PowerPoint)\nGestion de bases de données simples\nProduction documentaire professionnelle\nFormation des adultes\nDidactique de la bureautique',
            'matieres_principales': 'Traitement de texte avancé\nTableurs et fonctions\nPrésentations professionnelles\nIntroduction à internet\nPédagogie générale\nDidactique de la bureautique',
            'icone': 'computer',
            'ordre': 6,
        },
        {
            'nom': 'Communication Administrative',
            'slug': 'communication-administrative',
            'description_courte': 'Techniques de communication formelle, secrétariat moderne et correspondance professionnelle.',
            'description_longue': 'La filière Communication Administrative forme les instituteurs aux techniques du secrétariat moderne et de la communication professionnelle. Rédaction administrative, accueil, gestion documentaire et relations publiques sont au cœur de cette formation polyvalente.',
            'debouches': 'Instituteur en communication administrative. Formateur en secrétariat professionnel. Encadrement de cabinets de communication.',
            'competences_acquises': 'Rédaction administrative et juridique\nAccueil et communication interpersonnelle\nGestion documentaire et archivage\nCorrespondance professionnelle\nDidactique du secrétariat',
            'matieres_principales': 'Techniques d\'expression écrite\nCommunication orale et accueil\nDroit administratif\nGestion documentaire\nPédagogie\nDidactique du secrétariat',
            'icone': 'mail',
            'ordre': 7,
        },
    ]

    for filiere_data in filieres_data:
        Filiere.objects.get_or_create(
            ecole=eniet,
            slug=filiere_data['slug'],
            defaults=filiere_data,
        )


def supprimer_filieres(apps, schema_editor):
    """Rollback : supprime les filières créées."""
    Filiere = apps.get_model('ecoles', 'Filiere')
    Filiere.objects.filter(ecole__sigle='ENIET').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('ecoles', '0003_filiere'),
    ]

    operations = [
        migrations.RunPython(
            creer_filieres,
            reverse_code=supprimer_filieres,
        ),
    ]