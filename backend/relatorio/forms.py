# SeuApp/forms.py
from django import forms
from django.forms.models import inlineformset_factory
from .models import Relatorio, Imagem, Cliente

class RelatorioForm(forms.ModelForm):
    class Meta:
        model = Relatorio
        fields = ['hospital', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 4}),
        }

# CRIAÇÃO DO FORMSET PARA IMAGENS
ImagemFormSet = inlineformset_factory(
    Relatorio,
    Imagem,
    fields=('imagem',),
    extra=1,            # Define apenas 1 campo inicial, os outros serão via JS.
    can_delete=True     # Permite que o JS adicione um botão de 'Remover'.
)