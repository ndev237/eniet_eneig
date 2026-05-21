"""
Data migration : insère les données initiales du site.

Une "data migration" est différente d'une migration de schéma :
- Migration de schéma = changements de structure (tables, colonnes)
- Data migration = insertion/modification de données

Django les traite pareil : `migrate` exécute les deux dans l'ordre.
"""

from django.db import migrations


def creer_donnees_initiales(apps, schema_editor):
    """
    Crée les valeurs et membres de la direction par défaut.

    IMPORTANT : ne JAMAIS importer les modèles directement.
    Toujours utiliser apps.get_model() qui charge la version du modèle
    AU MOMENT de la migration (utile si on réexécute d'anciennes migrations).
    """
    Valeur = apps.get_model('pages', 'Valeur')
    MembreDirection = apps.get_model('pages', 'MembreDirection')
    SiteSettings = apps.get_model('pages', 'SiteSettings')

    # Créer les paramètres du site avec les valeurs par défaut
    # (déjà définies via default= dans le modèle)
    SiteSettings.objects.get_or_create(pk=1)

    # ============================================================
    # VALEURS DE L'ÉTABLISSEMENT
    # ============================================================
    valeurs_data = [
        {
            'titre': 'Excellence',
            'description': 'Nous formons des instituteurs d\'élite, capables de transmettre le savoir avec rigueur et passion.',
            'icone': 'star',
            'ordre': 1,
        },
        {
            'titre': 'Rigueur',
            'description': 'La discipline académique et professionnelle est au cœur de notre pédagogie.',
            'icone': 'shield',
            'ordre': 2,
        },
        {
            'titre': 'Intégrité',
            'description': 'L\'honnêteté intellectuelle et morale guide chacune de nos actions.',
            'icone': 'heart',
            'ordre': 3,
        },
        {
            'titre': 'Innovation',
            'description': 'Nous adoptons les meilleures méthodes pédagogiques modernes adaptées au contexte camerounais.',
            'icone': 'sparkle',
            'ordre': 4,
        },
    ]

    for valeur_data in valeurs_data:
        Valeur.objects.get_or_create(
            titre=valeur_data['titre'],
            defaults=valeur_data,
        )

    # ============================================================
    # DIRECTEUR PAR DÉFAUT (à modifier ensuite par l'admin)
    # ============================================================
    MembreDirection.objects.get_or_create(
        fonction='Directeur',
        defaults={
            'nom': 'M. le Directeur',
            'biographie': 'Diplômé en sciences de l\'éducation, le directeur de l\'ENIET/ENIEG cumule plus de 20 années d\'expérience dans la formation des instituteurs au Cameroun.',
            'citation': 'Notre mission est de former les éducateurs qui façonneront la prochaine génération camerounaise. Chaque élève-maître qui sort de notre établissement porte avec lui notre engagement pour l\'excellence professionnelle.',
            'est_directeur': True,
            'ordre': 1,
        },
    )


def supprimer_donnees_initiales(apps, schema_editor):
    """
    Fonction inverse pour 'migrate <app> 0001' (rollback).
    Optionnelle mais bonne pratique.
    """
    Valeur = apps.get_model('pages', 'Valeur')
    MembreDirection = apps.get_model('pages', 'MembreDirection')

    Valeur.objects.all().delete()
    MembreDirection.objects.filter(fonction='Directeur', nom='M. le Directeur').delete()


class Migration(migrations.Migration):
    """
    Migration qui dépend de 0001_initial (création des tables)
    et qui exécute la fonction Python ci-dessus.
    """

    dependencies = [
        ('pages', '0001_initial'),
    ]

    operations = [
        # RunPython exécute une fonction Python pendant la migration
        # Premier argument : fonction à exécuter en avant (migrate)
        # Second argument : fonction à exécuter en arrière (rollback)
        migrations.RunPython(
            creer_donnees_initiales,
            reverse_code=supprimer_donnees_initiales,
        ),
    ]