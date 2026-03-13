from django import forms
from .models import ExtensionRecord, NarrativeReport


class ExtensionRecordForm(forms.ModelForm):
    class Meta:
        model = ExtensionRecord
        fields = ['proposal', 'title', 'extension_type', 'team_members', 
                  'partner_community', 'location', 'status', 'start_date', 'end_date',
                  'beneficiary_count', 'description', 'output_documents', 'photos']
        widgets = {
            'proposal': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'extension_type': forms.Select(attrs={'class': 'form-select'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'partner_community': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'beneficiary_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'output_documents': forms.FileInput(attrs={'class': 'form-control'}),
            'photos': forms.FileInput(attrs={'class': 'form-control'}),
        }


class NarrativeReportForm(forms.ModelForm):
    class Meta:
        model = NarrativeReport
        fields = ['quarter', 'report_year', 'narrative']
        widgets = {
            'quarter': forms.Select(attrs={'class': 'form-select'}),
            'report_year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'}),
            'narrative': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Provide a detailed narrative report for this quarter here...'}),
        }
