from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Dashboard'

    def ready(self):
        """
        Méthode appelée par Django au démarrage.
        On importe nos modèles pour déclencher l'enregistrement des signals.

        Le simple fait d'importer le fichier models.py exécute les décorateurs
        @receiver qui enregistrent les listeners.
        """
        # Import retardé pour éviter les imports circulaires
        from . import models  # noqa: F401