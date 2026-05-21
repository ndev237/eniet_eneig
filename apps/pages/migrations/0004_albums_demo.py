"""
Crée des albums de démonstration avec des images placeholder.

NOTE PÉDAGOGIQUE :
On ne peut pas créer de vraies photos via une migration (les ImageField
attendent des fichiers physiques uploadés). Cette migration crée donc
seulement la STRUCTURE des albums.

L'admin uploadera ensuite les vraies photos depuis le dashboard.
Pour tester immédiatement, on créera des entrées Photo avec un chemin
d'image fictif - on les remplacera plus tard.
"""

from datetime import date

from django.db import migrations


def creer_albums_demo(apps, schema_editor):
    """Crée 3 albums de démonstration."""
    Album = apps.get_model('pages', 'Album')

    albums_data = [
        {
            'titre': 'Cérémonie de remise des diplômes 2025',
            'slug': 'remise-diplomes-2025',
            'description': 'Cérémonie officielle de remise des diplômes de la promotion 2025, en présence du Délégué Régional du MINESEC et des familles.',
            'date_evenement': date(2025, 7, 15),
            'est_a_la_une': True,
            'publie': True,
        },
        {
            'titre': 'Atelier filière Électricité',
            'slug': 'atelier-electricite-2026',
            'description': 'Atelier pratique des élèves-maîtres de la filière Électricité avec un partenaire industriel local.',
            'date_evenement': date(2026, 4, 28),
            'est_a_la_une': False,
            'publie': True,
        },
        {
            'titre': 'Visite des infrastructures',
            'slug': 'visite-infrastructures-2026',
            'description': 'Présentation des bâtiments, ateliers et salles de cours de notre établissement.',
            'date_evenement': date(2026, 2, 10),
            'est_a_la_une': False,
            'publie': True,
        },
    ]

    for album_data in albums_data:
        Album.objects.get_or_create(
            slug=album_data['slug'],
            defaults=album_data,
        )


def supprimer_albums_demo(apps, schema_editor):
    """Rollback."""
    Album = apps.get_model('pages', 'Album')
    Album.objects.filter(slug__in=[
        'remise-diplomes-2025',
        'atelier-electricite-2026',
        'visite-infrastructures-2026',
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        # ⚠️ Adapte ce nom au numéro de ta migration précédente !
        ('pages', '0003_album_photo'),
    ]

    operations = [
        migrations.RunPython(
            creer_albums_demo,
            reverse_code=supprimer_albums_demo,
        ),
    ]
