from django import forms
from django.utils.translation import gettext_lazy as _

from .models import MessageContact


class ContactForm(forms.ModelForm):
    """
    Formulaire de contact basé sur le modèle MessageContact.

    Pourquoi ModelForm et pas Form ?
    - ModelForm hérite automatiquement des champs et validations du modèle
    - Moins de duplication de code
    - Si on ajoute un champ au modèle, le formulaire s'adapte

    On précise via Meta quels champs on veut exposer à l'utilisateur final
    (on exclut statut, note_interne qui sont réservés à l'admin).
    """

    class Meta:
        model = MessageContact
        # Champs exposés dans le formulaire public
        # IMPORTANT : statut et note_interne ne doivent JAMAIS être ici
        # Sinon l'utilisateur pourrait les manipuler (faille de sécurité)
        fields = ['nom', 'email', 'telephone', 'sujet', 'message']

        # Personnalisation des widgets HTML pour le rendu Tailwind
        # Un "widget" est l'élément HTML utilisé (input, textarea, select)
        # On y attache nos classes CSS Tailwind
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-primary/15 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-ink placeholder:text-ink/40',
                'placeholder': _('Votre nom complet'),
                'autocomplete': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-primary/15 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-ink placeholder:text-ink/40',
                'placeholder': 'votre.email@exemple.com',
                'autocomplete': 'email',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-primary/15 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-ink placeholder:text-ink/40',
                'placeholder': '+237 6XX XX XX XX',
                'autocomplete': 'tel',
            }),
            'sujet': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-primary/15 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-ink',
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-primary/15 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-ink placeholder:text-ink/40 resize-none',
                'placeholder': _('Décrivez votre demande...'),
                'rows': 6,
            }),
        }

        # Labels personnalisés - surchargent ceux du modèle si besoin
        labels = {
            'nom': _('Nom complet'),
            'email': _('Adresse email'),
            'telephone': _('Téléphone'),
            'sujet': _('Objet du message'),
            'message': _('Votre message'),
        }

    def clean_message(self):
        """
        Validation personnalisée pour le champ 'message'.

        Convention Django : une méthode nommée clean_<nomduchamp> est
        automatiquement appelée pour valider ce champ spécifique.
        Elle reçoit la valeur nettoyée, peut lever ValidationError,
        et doit retourner la valeur (modifiée ou non).
        """
        message = self.cleaned_data.get('message', '').strip()

        # Refuser les messages trop courts (probable spam ou test)
        if len(message) < 10:
            raise forms.ValidationError(
                _('Votre message doit contenir au moins 10 caractères.')
            )

        # Refuser les messages trop longs (limite raisonnable)
        if len(message) > 5000:
            raise forms.ValidationError(
                _('Votre message ne peut pas dépasser 5000 caractères.')
            )

        return message