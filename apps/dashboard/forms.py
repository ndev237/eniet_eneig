from django import forms
from django.utils.translation import gettext_lazy as _
from tinymce.widgets import TinyMCE
from apps.pages.models import SiteSettings,Album
from apps.blog.models import Article, Categorie, Tag
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from .models import Profil
# ============================================================
# CLASSES CSS RÉUTILISABLES POUR LES FORMULAIRES
# ============================================================
# On définit les classes Tailwind une seule fois pour rester DRY
INPUT_CLASSES = (
    'w-full px-4 py-3 bg-white border border-primary/15 '
    'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 '
    'transition-all text-ink placeholder:text-ink/40'
)

SELECT_CLASSES = (
    'w-full px-4 py-3 bg-white border border-primary/15 '
    'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 '
    'transition-all text-ink'
)

TEXTAREA_CLASSES = (
    'w-full px-4 py-3 bg-white border border-primary/15 '
    'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 '
    'transition-all text-ink placeholder:text-ink/40 resize-y'
)


class ArticleForm(forms.ModelForm):
    """
    Formulaire de création/édition d'un article.

    On utilise ModelForm car il génère automatiquement les champs
    depuis le modèle Article. On personnalise les widgets pour
    avoir un rendu Tailwind cohérent.

    Champs exclus du formulaire (gérés automatiquement) :
    - auteur : assigné à l'utilisateur connecté dans la vue
    - nombre_vues : auto-incrémenté côté public
    - created_at / updated_at : auto-gérés
    """

    class Meta:
        model = Article
        fields = [
            'titre', 'slug', 'resume', 'contenu',
            'image_une', 'image_une_alt',
            'categorie', 'tags',
            'statut', 'date_publication', 'est_a_la_une',
        ]

        widgets = {
            # Texte simple
            'titre': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': _('Titre accrocheur de l\'article'),
            }),
            'slug': forms.TextInput(attrs={
                'class': INPUT_CLASSES + ' font-mono text-sm',
                'placeholder': _('genere-automatiquement-depuis-titre'),
            }),
            'resume': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 3,
                'placeholder': _('Phrase d\'accroche affichée sur les listes et partages sociaux (max 300 caractères)'),
                'maxlength': 300,
            }),

            # ============================================================
            # ÉDITEUR RICHE pour le contenu (TinyMCE)
            # ============================================================
            'contenu': TinyMCE(attrs={'cols': 80, 'rows': 30}),

            # Image (input file natif HTML, on stylise ailleurs)
            'image_une_alt': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': _('Description de l\'image (accessibilité, SEO)'),
            }),

            # Sélecteurs
            'categorie': forms.Select(attrs={'class': SELECT_CLASSES}),
            'statut': forms.Select(attrs={'class': SELECT_CLASSES}),

            # ManyToMany pour les tags : on utilisera un widget custom JS plus tard
            # Pour l'instant : SelectMultiple natif
            'tags': forms.SelectMultiple(attrs={
                'class': SELECT_CLASSES + ' h-32',
                'size': 8,
            }),

            # DateTime
            'date_publication': forms.DateTimeInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'datetime-local',  # ← input HTML5 natif
            }),

            # Checkbox
            'est_a_la_une': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary focus:ring-primary border-primary/30',
            }),
        }

        labels = {
            'titre': _('Titre de l\'article'),
            'slug': _('Slug URL'),
            'resume': _('Résumé / accroche'),
            'contenu': _('Contenu de l\'article'),
            'image_une': _('Image à la une'),
            'image_une_alt': _('Texte alternatif de l\'image'),
            'categorie': _('Catégorie'),
            'tags': _('Tags'),
            'statut': _('Statut de publication'),
            'date_publication': _('Date de publication'),
            'est_a_la_une': _('Mettre à la une'),
        }

        help_texts = {
            'slug': _('Laissez vide pour génération automatique depuis le titre'),
            'date_publication': _('Pour programmer une publication future'),
            'est_a_la_une': _('Affiche cet article en avant sur la page d\'accueil'),
        }

    def __init__(self, *args, **kwargs):
        """
        Personnalisation à l'initialisation :
        - Le slug devient optionnel (sera auto-généré)
        - Format de date par défaut pour datetime-local
        """
        super().__init__(*args, **kwargs)

        # Le slug est optionnel dans le formulaire (auto-généré dans save)
        self.fields['slug'].required = False

        # Format ISO pour datetime-local (sinon l'input HTML5 ne reconnaît pas)
        if self.instance and self.instance.date_publication:
            self.initial['date_publication'] = self.instance.date_publication.strftime('%Y-%m-%dT%H:%M')

    def clean_resume(self):
        """Validation custom : minimum 20 caractères pour le résumé."""
        resume = self.cleaned_data.get('resume', '').strip()
        if len(resume) < 20:
            raise forms.ValidationError(
                _('Le résumé doit contenir au moins 20 caractères.')
            )
        return resume

    def clean_titre(self):
        """Validation : titre minimum 5 caractères."""
        titre = self.cleaned_data.get('titre', '').strip()
        if len(titre) < 5:
            raise forms.ValidationError(
                _('Le titre doit contenir au moins 5 caractères.')
            )
        return titre


class SiteSettingsForm(forms.ModelForm):
    """
    Formulaire d'édition des paramètres globaux du site.

    Particularité : SiteSettings est un singleton (un seul objet).
    On ne crée jamais de nouveau, on modifie toujours l'unique instance.

    On expose TOUS les champs modifiables, organisés logiquement.
    Les champs created_at/updated_at sont exclus (auto-gérés).
    """

    class Meta:
        model = SiteSettings
        # On liste explicitement les champs pour contrôler l'ordre
        # et exclure created_at/updated_at
        fields = [
            # Identité
            'nom_etablissement', 'devise', 'description_courte',
            # Coordonnées
            'email_principal', 'email_contact',
            'telephone_1', 'telephone_2', 'telephone_3',
            'adresse_ligne_1', 'adresse_ligne_2', 'boite_postale',
            # GPS
            'latitude', 'longitude',
            # Horaires
            'horaires_semaine', 'horaires_samedi',
            # Réseaux sociaux
            'facebook_url', 'instagram_url', 'youtube_url', 'linkedin_url',
            # Agréments
            'arrete_eniet', 'arrete_enieg',
            # Année scolaire
            'annee_scolaire',
        ]

        widgets = {
            # Identité
            'nom_etablissement': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'devise': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'description_courte': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES, 'rows': 3,
            }),

            # Coordonnées
            'email_principal': forms.EmailInput(attrs={'class': INPUT_CLASSES}),
            'email_contact': forms.EmailInput(attrs={'class': INPUT_CLASSES}),
            'telephone_1': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'telephone_2': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'telephone_3': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'adresse_ligne_1': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'adresse_ligne_2': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'boite_postale': forms.TextInput(attrs={'class': INPUT_CLASSES}),

            # GPS
            'latitude': forms.NumberInput(attrs={
                'class': INPUT_CLASSES, 'step': 'any',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': INPUT_CLASSES, 'step': 'any',
            }),

            # Horaires
            'horaires_semaine': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'horaires_samedi': forms.TextInput(attrs={'class': INPUT_CLASSES}),

            # Réseaux sociaux
            'facebook_url': forms.URLInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'https://facebook.com/...',
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'https://instagram.com/...',
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'https://youtube.com/...',
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': 'https://linkedin.com/...',
            }),

            # Agréments
            'arrete_eniet': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'arrete_enieg': forms.TextInput(attrs={'class': INPUT_CLASSES}),

            # Année scolaire
            'annee_scolaire': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 'placeholder': '2025-2026',
            }),
        }

    def clean_annee_scolaire(self):
        """
        Validation du format de l'année scolaire : YYYY-YYYY.
        Ex: 2025-2026 est valide, 2025 ne l'est pas.
        """
        annee = self.cleaned_data.get('annee_scolaire', '').strip()

        # Vérification basique du format avec une regex simple
        import re
        if not re.match(r'^\d{4}-\d{4}$', annee):
            raise forms.ValidationError(
                "Le format attendu est AAAA-AAAA (ex: 2025-2026)."
            )

        # Vérification cohérence : 2e année = 1re année + 1
        debut, fin = annee.split('-')
        if int(fin) != int(debut) + 1:
            raise forms.ValidationError(
                "La seconde année doit suivre immédiatement la première (ex: 2025-2026)."
            )

        return annee


class AlbumForm(forms.ModelForm):
    """
    Formulaire de création/édition d'un album photo.

    Note : les photos ne sont PAS gérées par ce formulaire.
    Elles sont uploadées séparément via un endpoint AJAX dédié,
    car on veut permettre l'upload multiple et le drag & drop.
    """

    class Meta:
        model = Album
        fields = [
            'titre', 'slug', 'description', 'date_evenement',
            'couverture', 'est_a_la_une', 'publie',
        ]

        widgets = {
            'titre': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Ex: Cérémonie de remise des diplômes 2025',
            }),
            'slug': forms.TextInput(attrs={
                'class': INPUT_CLASSES + ' font-mono text-sm',
                'placeholder': 'genere-automatiquement',
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 4,
                'placeholder': 'Décrivez l\'événement, son contexte...',
            }),
            'date_evenement': forms.DateInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'date',  # ← input date HTML5 natif
            }),
            'est_a_la_une': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary focus:ring-primary border-primary/30',
            }),
            'publie': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary focus:ring-primary border-primary/30',
            }),
        }

        labels = {
            'titre': 'Titre de l\'album',
            'slug': 'Slug URL',
            'description': 'Description',
            'date_evenement': 'Date de l\'événement',
            'couverture': 'Photo de couverture',
            'est_a_la_une': 'Mettre à la une',
            'publie': 'Publier l\'album',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le slug est optionnel (auto-généré dans le save du modèle)
        self.fields['slug'].required = False

        # Format ISO pour l'input date HTML5
        if self.instance and self.instance.pk and self.instance.date_evenement:
            self.initial['date_evenement'] = self.instance.date_evenement.strftime('%Y-%m-%d')

    def save(self, *args, **kwargs):
        """
        Génère le slug automatiquement si vide (avant le save du modèle).
        """
        from django.utils.text import slugify
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.titre)
        if kwargs.get('commit', True):
            instance.save()
        return instance


class UtilisateurCreationForm(forms.Form):
    """
    Formulaire de création d'un nouvel utilisateur.

    On utilise forms.Form (pas ModelForm) car on doit créer DEUX objets :
    - Un User (auth Django)
    - Son Profil associé (créé automatiquement par le signal)

    On gère aussi la définition du mot de passe initial.
    """

    prenom = forms.CharField(
        label='Prénom',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Jean',
        }),
    )

    nom = forms.CharField(
        label='Nom',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Dupont',
        }),
    )

    username = forms.CharField(
        label='Identifiant de connexion',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'jean.dupont',
        }),
        help_text='Sans espaces ni accents. Servira pour se connecter.',
    )

    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'jean.dupont@exemple.com',
        }),
    )

    role = forms.ChoiceField(
        label='Rôle',
        choices=Profil.Role.choices,
        initial=Profil.Role.EDITEUR,
        widget=forms.Select(attrs={'class': SELECT_CLASSES}),
        help_text='Détermine les droits de l\'utilisateur.',
    )

    fonction = forms.CharField(
        label='Fonction',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Ex: Responsable communication',
        }),
    )

    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        }),
        help_text='Au moins 8 caractères.',
    )

    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        }),
    )

    def clean_username(self):
        """Vérifie que l'identifiant n'existe pas déjà."""
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Cet identifiant est déjà utilisé.")
        return username

    def clean_email(self):
        """Vérifie que l'email n'est pas déjà utilisé."""
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean_password1(self):
        """Validation de la robustesse du mot de passe."""
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit faire au moins 8 caractères.")
        return password

    def clean(self):
        """
        Validation globale : les deux mots de passe doivent correspondre.

        La méthode clean() (sans suffixe) valide le formulaire dans son
        ensemble, après les clean_<field> individuels. Utile pour valider
        des combinaisons de champs.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            # add_error attache l'erreur à un champ spécifique
            self.add_error('password2', "Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self):
        """
        Crée le User et configure son Profil.

        Note : le Profil est créé automatiquement par le signal post_save
        (défini dans models.py). On le récupère ensuite pour le configurer.
        """
        # create_user hash automatiquement le mot de passe (sécurité)
        # NE JAMAIS faire User(password=...) qui stockerait en clair !
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['prenom'],
            last_name=self.cleaned_data['nom'],
        )

        # Le signal a créé le profil, on le configure
        profil = user.profil
        profil.role = self.cleaned_data['role']
        profil.fonction = self.cleaned_data.get('fonction', '')
        profil.save()

        return user


class UtilisateurEditForm(forms.ModelForm):
    """
    Formulaire d'édition d'un utilisateur existant.

    On édite les infos du User (nom, prénom, email) + le rôle/fonction
    du Profil. Le mot de passe est géré séparément.
    """

    # Champs du Profil (pas dans le modèle User)
    role = forms.ChoiceField(
        label='Rôle',
        choices=Profil.Role.choices,
        widget=forms.Select(attrs={'class': SELECT_CLASSES}),
    )

    fonction = forms.CharField(
        label='Fonction',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Adresse email',
        }

    def __init__(self, *args, **kwargs):
        """Pré-remplit les champs du profil depuis l'instance User."""
        super().__init__(*args, **kwargs)
        # Si on édite un user existant, on charge ses données de profil
        if self.instance and self.instance.pk and hasattr(self.instance, 'profil'):
            self.fields['role'].initial = self.instance.profil.role
            self.fields['fonction'].initial = self.instance.profil.fonction

    def clean_email(self):
        """Vérifie l'unicité de l'email (sauf pour l'utilisateur courant)."""
        email = self.cleaned_data['email'].strip().lower()
        # exclude(pk=...) : on autorise l'utilisateur à garder son propre email
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def save(self, commit=True):
        """Sauvegarde le User + met à jour son Profil."""
        user = super().save(commit=commit)

        if commit:
            # Met à jour le profil
            profil = user.profil
            profil.role = self.cleaned_data['role']
            profil.fonction = self.cleaned_data.get('fonction', '')
            profil.save()

        return user


class MotDePasseForm(SetPasswordForm):
    """
    Formulaire de changement de mot de passe.

    Hérite de SetPasswordForm de Django qui gère déjà :
    - Les deux champs (nouveau + confirmation)
    - La validation de correspondance
    - Le hashage sécurisé

    On personnalise juste les widgets pour le style Tailwind.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des widgets hérités
        self.fields['new_password1'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        })
        # Labels en français
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le nouveau mot de passe'


class MonProfilForm(forms.ModelForm):
    """
    Formulaire d'édition du profil personnel.

    Différence avec UtilisateurEditForm :
    - Ne permet PAS de changer le rôle (l'utilisateur ne s'auto-promeut pas)
    - Inclut la photo de profil et la biographie
    - Accessible par tous, pas seulement super-admin
    """

    # Champs du modèle User
    first_name = forms.CharField(
        label='Prénom',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES}),
    )
    last_name = forms.CharField(
        label='Nom',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES}),
    )
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES}),
    )

    class Meta:
        model = Profil
        # Champs du Profil modifiables par l'utilisateur lui-même
        fields = ['photo', 'fonction', 'telephone', 'biographie']
        widgets = {
            'fonction': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'telephone': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'biographie': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES, 'rows': 4,
            }),
        }
        labels = {
            'fonction': 'Fonction',
            'telephone': 'Téléphone',
            'biographie': 'Biographie',
        }

    def __init__(self, *args, **kwargs):
        """Pré-remplit les champs User depuis l'instance liée."""
        super().__init__(*args, **kwargs)
        # self.instance est le Profil, on accède au User via .user
        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        from django.contrib.auth.models import User
        # On exclut l'utilisateur courant de la vérification d'unicité
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def save(self, commit=True):
        """Sauvegarde le Profil + met à jour le User lié."""
        profil = super().save(commit=commit)

        if commit:
            user = profil.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()

        return profil


class MonMotDePasseForm(PasswordChangeForm):
    """
    Changement de SON PROPRE mot de passe.

    Différence avec MotDePasseForm :
    - Hérite de PasswordChangeForm (pas SetPasswordForm)
    - Demande l'ancien mot de passe pour confirmation (sécurité)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['old_password', 'new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs.update({
                'class': INPUT_CLASSES,
                'placeholder': '••••••••',
            })
        self.fields['old_password'].label = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le nouveau mot de passe'