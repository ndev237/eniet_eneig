"""
Backend d'authentification par ADRESSE EMAIL.

Django appelle chaque backend enregistré dans AUTHENTICATION_BACKENDS avec
la même signature `authenticate(request, username=..., password=...)`. On
récupère donc la chaîne saisie dans le champ « username » du formulaire,
et on la traite comme un email : lookup case-insensitive sur User.email,
puis vérification du mot de passe.

Deux garde-fous importants :

  - MultipleObjectsReturned : deux comptes ayant le même email (le modèle
    User de Django n'impose pas l'unicité) → on refuse d'authentifier
    plutôt que de choisir arbitrairement. La console d'admin doit résoudre
    la collision avant que ces comptes puissent se connecter.

  - Mitigation d'attaque temporelle (timing attack) : si aucun utilisateur
    n'existe pour cet email, on exécute quand même un set_password vide.
    Cela évite qu'un attaquant devine par la latence de la réponse quels
    emails existent en base.

On hérite de ModelBackend uniquement pour bénéficier de sa méthode
`get_user(user_id)` (utilisée par le middleware de session pour
recharger request.user à chaque requête). Sa méthode `authenticate`,
elle, est complètement remplacée ci-dessous.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Authentification par email au lieu du username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Django peut aussi passer email= au lieu de username= sur certains
        # points d'entrée custom : on couvre les deux.
        email = username or kwargs.get('email')
        if email is None or password is None:
            return None

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email.strip())
        except UserModel.DoesNotExist:
            # Timing-attack mitigation : on paie le coût du hachage même
            # quand l'utilisateur n'existe pas, pour que la latence de la
            # réponse ne trahisse pas l'existence de l'email.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # Collision d'emails en base → refus catégorique. L'admin doit
            # démêler avant que ces comptes puissent se connecter.
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
