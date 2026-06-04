"""
Crée un profil pour tous les users existants qui n'en ont pas.

Cette migration de données rattrape les comptes créés AVANT
l'installation du signal post_save.
"""

from django.db import migrations


def creer_profils_existants(apps, schema_editor):
    """Crée un profil pour chaque user qui n'en a pas."""
    User = apps.get_model('auth', 'User')
    Profil = apps.get_model('dashboard', 'Profil')

    for user in User.objects.all():
        if not Profil.objects.filter(user=user).exists():
            # Le superuser devient super_admin, les autres sont éditeurs
            role = 'super_admin' if user.is_superuser else 'editeur'
            Profil.objects.create(user=user, role=role)


def supprimer_profils(apps, schema_editor):
    """Rollback : ne fait rien (on garde les profils par sécurité)."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            creer_profils_existants,
            reverse_code=supprimer_profils,
        ),
    ]