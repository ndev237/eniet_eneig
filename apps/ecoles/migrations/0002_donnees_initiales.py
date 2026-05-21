"""
Insère les données officielles ENIEG et ENIET depuis les PDF.
Tarifs et conditions extraits des arrêtés du MINESEC.
"""

from django.db import migrations


def creer_donnees_initiales(apps, schema_editor):
    """Crée ENIEG, ENIET, leurs tranches et les documents requis."""
    Ecole = apps.get_model('ecoles', 'Ecole')
    TranchePaiement = apps.get_model('ecoles', 'TranchePaiement')
    DocumentRequis = apps.get_model('ecoles', 'DocumentRequis')
    FAQ = apps.get_model('ecoles', 'FAQ')

    # ============================================================
    # ÉCOLE 1 : ENIEG
    # ============================================================
    enieg, _ = Ecole.objects.get_or_create(
        sigle='ENIEG',
        defaults={
            'nom': 'École Normale d\'Instituteurs de l\'Enseignement Général',
            'slug': 'enieg',
            'type_ecole': 'general',
            'diplome_prepare': 'CAPIEMP',
            'diplome_complet': 'Certificat d\'Aptitude Pédagogique d\'Instituteurs de l\'Enseignement Maternel et Primaire Général',
            'description_courte': 'Formation des futurs maîtres de l\'école maternelle et primaire. Concours ouvert aux titulaires du Baccalauréat de l\'enseignement général.',
            'description_longue': 'L\'ENIEG forme les instituteurs de l\'enseignement général en 2 ans. La formation prépare au CAPIEMP, diplôme officiel reconnu par l\'État pour enseigner dans les écoles maternelles et primaires du Cameroun. Le recrutement se fait sur concours, ouvert aux titulaires du Baccalauréat de l\'enseignement général.',
            'pre_requis': 'Baccalauréat de l\'enseignement général ou diplôme équivalent reconnu par le MINESEC.',
            'duree_formation': '2 ans',
            'frais_concours': 12000,
            'frais_inscription_non_remboursable': 25000,
            'matiere_oeuvre': 0,  # ENIEG n'a pas de matière d'œuvre
            'ordre': 1,
            'actif': True,
        },
    )

    # Tranches ENIEG - 1ère année (Total : 225 000 FCFA)
    tranches_enieg_an1 = [
        {'numero_tranche': 1, 'libelle': '1ère tranche', 'montant': 100000, 'echeance': 'À l\'inscription', 'ordre': 1},
        {'numero_tranche': 2, 'libelle': '2ème tranche', 'montant': 80000, 'echeance': 'Le 10 décembre', 'ordre': 2},
        {'numero_tranche': 3, 'libelle': '3ème tranche', 'montant': 20000, 'echeance': 'Le 9 janvier', 'ordre': 3},
    ]
    for tranche_data in tranches_enieg_an1:
        TranchePaiement.objects.get_or_create(
            ecole=enieg,
            annee=1,
            numero_tranche=tranche_data['numero_tranche'],
            defaults=tranche_data,
        )

    # Tranches ENIEG - 2ème année (Total : 255 000 FCFA)
    tranches_enieg_an2 = [
        {'numero_tranche': 1, 'libelle': '1ère tranche', 'montant': 150000, 'echeance': 'À l\'inscription', 'ordre': 1},
        {'numero_tranche': 2, 'libelle': '2ème tranche', 'montant': 60000, 'echeance': 'Le 10 décembre', 'ordre': 2},
        {'numero_tranche': 3, 'libelle': '3ème tranche', 'montant': 20000, 'echeance': 'Le 9 janvier', 'ordre': 3},
    ]
    for tranche_data in tranches_enieg_an2:
        TranchePaiement.objects.get_or_create(
            ecole=enieg,
            annee=2,
            numero_tranche=tranche_data['numero_tranche'],
            defaults=tranche_data,
        )

    # ============================================================
    # ÉCOLE 2 : ENIET
    # ============================================================
    eniet, _ = Ecole.objects.get_or_create(
        sigle='ENIET',
        defaults={
            'nom': 'École Normale d\'Instituteurs de l\'Enseignement Technique',
            'slug': 'eniet',
            'type_ecole': 'technique',
            'diplome_prepare': 'CAPIET',
            'diplome_complet': 'Certificat d\'Aptitude Pédagogique d\'Instituteurs de l\'Enseignement Technique',
            'description_courte': 'Formation des instituteurs de l\'enseignement technique en 7 filières spécialisées. Ouvert aux titulaires de BT, PBT, BP ou Bac technique.',
            'description_longue': 'L\'ENIET forme les instituteurs de l\'enseignement technique en 2 ans. Sept filières professionnelles sont proposées : Électricité, Construction (Maçonnerie et Béton armé), Couture, Économie Sociale et Familiale, Comptabilité et Gestion, Bureautique, et Communication Administrative.',
            'pre_requis': 'BT, PBT, BP ou Baccalauréat de l\'enseignement technique industriel et commercial.',
            'duree_formation': '2 ans',
            'frais_concours': 12000,
            'frais_inscription_non_remboursable': 25000,
            'matiere_oeuvre': 25000,  # ENIET a une matière d'œuvre
            'ordre': 2,
            'actif': True,
        },
    )

    # Tranches ENIET - 1ère année (Total : 300 000 FCFA)
    tranches_eniet_an1 = [
        {'numero_tranche': 1, 'libelle': '1ère tranche', 'montant': 150000, 'echeance': 'À l\'inscription', 'ordre': 1},
        {'numero_tranche': 2, 'libelle': '2ème tranche', 'montant': 100000, 'echeance': 'Le 10 décembre', 'ordre': 2},
    ]
    for tranche_data in tranches_eniet_an1:
        TranchePaiement.objects.get_or_create(
            ecole=eniet,
            annee=1,
            numero_tranche=tranche_data['numero_tranche'],
            defaults=tranche_data,
        )

    # Tranches ENIET - 2ème année (Total : 350 000 FCFA)
    tranches_eniet_an2 = [
        {'numero_tranche': 1, 'libelle': '1ère tranche', 'montant': 175000, 'echeance': 'À l\'inscription', 'ordre': 1},
        {'numero_tranche': 2, 'libelle': '2ème tranche', 'montant': 125000, 'echeance': 'Le 10 décembre', 'ordre': 2},
    ]
    for tranche_data in tranches_eniet_an2:
        TranchePaiement.objects.get_or_create(
            ecole=eniet,
            annee=2,
            numero_tranche=tranche_data['numero_tranche'],
            defaults=tranche_data,
        )

    # ============================================================
    # DOCUMENTS REQUIS POUR LE DOSSIER
    # ============================================================
    documents = [
        {'libelle': 'Photocopie de la Carte Nationale d\'Identité', 'description': 'Recto-verso, en cours de validité',
         'ordre': 1},
        {'libelle': 'Photocopie certifiée conforme du Baccalauréat', 'description': 'Ou diplôme équivalent',
         'ordre': 2},
        {'libelle': 'Photocopie certifiée conforme de l\'acte de naissance', 'description': 'De moins de 3 mois',
         'ordre': 3},
        {'libelle': 'Quatre (4) photos 4×4', 'description': 'Récentes, fond uni', 'ordre': 4},
        {'libelle': 'Fiche d\'inscription remplie sur place', 'description': '', 'ordre': 5},
        {'libelle': 'Demande manuscrite adressée au Directeur', 'description': 'Datée et signée', 'ordre': 6},
        {'libelle': 'Frais de concours : 12 000 FCFA', 'description': 'Non remboursable', 'ordre': 7},
    ]
    for doc_data in documents:
        DocumentRequis.objects.get_or_create(
            libelle=doc_data['libelle'],
            defaults=doc_data,
        )

    # ============================================================
    # QUESTIONS FRÉQUENTES
    # ============================================================
    faqs = [
        {
            'question': 'Quelles sont les conditions pour s\'inscrire au concours ?',
            'reponse': 'Pour l\'ENIEG, il faut être titulaire du Baccalauréat de l\'enseignement général. Pour l\'ENIET, il faut être titulaire d\'un BT, PBT, BP ou Baccalauréat de l\'enseignement technique industriel et commercial.',
            'categorie': 'admission',
            'ordre': 1,
        },
        {
            'question': 'Quand les inscriptions au concours sont-elles ouvertes ?',
            'reponse': 'Les inscriptions au concours sont généralement ouvertes entre juin et septembre de chaque année. Consultez la page d\'accueil pour les dates précises de l\'année en cours.',
            'categorie': 'admission',
            'ordre': 2,
        },
        {
            'question': 'Combien coûte la scolarité ?',
            'reponse': 'Pour l\'ENIEG, la scolarité de 1ère année est de 225 000 FCFA (hors inscription non remboursable). Pour l\'ENIET, elle est de 300 000 FCFA. Les frais sont payables en plusieurs tranches selon un échéancier précis.',
            'categorie': 'frais',
            'ordre': 3,
        },
        {
            'question': 'Les frais d\'inscription sont-ils remboursables ?',
            'reponse': 'Non. Les frais d\'inscription (25 000 FCFA) et les frais de concours (12 000 FCFA) ne sont jamais remboursables, quelle que soit la situation.',
            'categorie': 'frais',
            'ordre': 4,
        },
        {
            'question': 'Quelle est la durée de la formation ?',
            'reponse': 'La durée de la formation est de 2 ans, en cours du jour (formation continue), aussi bien pour l\'ENIEG que pour l\'ENIET.',
            'categorie': 'formation',
            'ordre': 5,
        },
        {
            'question': 'Les diplômes sont-ils reconnus par l\'État ?',
            'reponse': 'Oui. Notre établissement est officiellement agréé par le Ministère des Enseignements Secondaires (MINESEC). Les diplômes CAPIEMP et CAPIET sont délivrés par l\'État et reconnus dans tout le Cameroun.',
            'categorie': 'formation',
            'ordre': 6,
        },
    ]
    for faq_data in faqs:
        FAQ.objects.get_or_create(
            question=faq_data['question'],
            defaults=faq_data,
        )


def supprimer_donnees_initiales(apps, schema_editor):
    """Rollback : supprime toutes les données initiales."""
    Ecole = apps.get_model('ecoles', 'Ecole')
    DocumentRequis = apps.get_model('ecoles', 'DocumentRequis')
    FAQ = apps.get_model('ecoles', 'FAQ')

    # Note : grâce à on_delete=CASCADE sur TranchePaiement,
    # supprimer une école supprime aussi ses tranches automatiquement
    Ecole.objects.filter(sigle__in=['ENIEG', 'ENIET']).delete()
    DocumentRequis.objects.all().delete()
    FAQ.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('ecoles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            creer_donnees_initiales,
            reverse_code=supprimer_donnees_initiales,
        ),
    ]