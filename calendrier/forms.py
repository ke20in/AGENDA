from django import forms
from .models import Activite

class ActiviteForm(forms.ModelForm):
    class Meta:
        model = Activite
        fields = ['activite', 'date_debut', 'date_fin', 'object', 'document', 'contact', 'email']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs obligatoires sauf 'objet', 'document', 'contact' et 'email'
        for field_name, field in self.fields.items():
            if field_name not in ['object', 'document', 'contact', 'email']:
                field.required = True
            else:
                field.required = False