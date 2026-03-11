from django import forms
from .models import ResearchRecord


class ResearchRecordForm(forms.ModelForm):
    class Meta:
        model = ResearchRecord
        fields = ['proposal', 'co_researchers', 'status', 'start_date', 'end_date',
                  'funding_source', 'funding_amount', 'output_description', 'publication_link']
        widgets = {
            'proposal': forms.Select(attrs={'class': 'form-select'}),
            'co_researchers': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'funding_source': forms.TextInput(attrs={'class': 'form-control'}),
            'funding_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'output_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'publication_link': forms.URLInput(attrs={'class': 'form-control'}),
        }
