from django import forms
from .models import Proposal, ProposalStatus, PROPOSAL_REQUIREMENT_CHOICES
from users.models import CustomUser, UserRole


class ProposalForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['research_staff'].required = False
        if user and user.is_research_extension_staff:
            self.fields['faculty_author'] = forms.ModelChoiceField(
                queryset=CustomUser.objects.filter(role=UserRole.FACULTY, is_active=True).order_by('last_name', 'first_name', 'username'),
                required=True,
                label='Faculty Author',
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white'
                }),
            )
        elif 'faculty_author' in self.fields:
            self.fields.pop('faculty_author')

    class Meta:
        model = Proposal
        fields = ['title', 'abstract', 'full_description', 'proposal_type',
                  'research_staff', 'proposal_document', 'budget_pdf', 'supporting_image', 'faculty_author']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Enter your proposal title'
            }),
            'abstract': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 5,
                'placeholder': 'Provide a brief summary of your proposal (min 50 characters)'
            }),
            'full_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 8,
                'placeholder': 'Provide comprehensive details about your proposal'
            }),
            'proposal_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white'
            }),
            'research_staff': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white'
            }),
            'proposal_document': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            'budget_pdf': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100'
            }),
            'supporting_image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100'
            }),
        }


class ProposalReviewForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            (ProposalStatus.APPROVED, 'Approve'),
            (ProposalStatus.REJECTED, 'Reject and request resubmission'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    missing_requirements = forms.MultipleChoiceField(
        choices=PROPOSAL_REQUIREMENT_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    custom_requirements = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
            'rows': 3,
            'placeholder': 'Add one custom requirement per line'
        })
    )

    class Meta:
        model = Proposal
        fields = ['status', 'review_notes']
        widgets = {
            'review_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 4,
                'placeholder': 'Provide feedback for the author'
            }),
}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.status == ProposalStatus.RECOMMENDED_APPROVAL and not self.is_bound:
            self.fields['status'].initial = ProposalStatus.APPROVED

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        review_notes = (cleaned_data.get('review_notes') or '').strip()
        missing_requirements = cleaned_data.get('missing_requirements') or []
        custom_requirements = [
            line.strip()
            for line in (cleaned_data.get('custom_requirements') or '').splitlines()
            if line.strip()
        ]

        if status == ProposalStatus.REJECTED:
            if not review_notes:
                self.add_error('review_notes', 'Review notes are required when rejecting a proposal.')
            if not missing_requirements and not custom_requirements:
                self.add_error('missing_requirements', 'Select at least one missing requirement or add a custom requirement.')

        cleaned_data['custom_requirements_list'] = custom_requirements
        return cleaned_data


class ProposalRecommendationForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            (ProposalStatus.RECOMMENDED_APPROVAL, 'Recommend for admin approval'),
            (ProposalStatus.RECOMMENDED_REVISION, 'Request revision or resubmission'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    missing_requirements = forms.MultipleChoiceField(
        choices=PROPOSAL_REQUIREMENT_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    custom_requirements = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
            'rows': 3,
            'placeholder': 'Add one custom requirement per line'
        })
    )

    class Meta:
        model = Proposal
        fields = ['status', 'recommendation_notes']
        widgets = {
            'recommendation_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 4,
                'placeholder': 'Explain your recommendation for the admin or the revisions needed from faculty'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        notes = (cleaned_data.get('recommendation_notes') or '').strip()
        missing_requirements = cleaned_data.get('missing_requirements') or []
        custom_requirements = [
            line.strip()
            for line in (cleaned_data.get('custom_requirements') or '').splitlines()
            if line.strip()
        ]
        if status == ProposalStatus.RECOMMENDED_REVISION and not notes:
            self.add_error('recommendation_notes', 'Recommendation notes are required when requesting revision.')
        if status == ProposalStatus.RECOMMENDED_REVISION and not missing_requirements and not custom_requirements:
            self.add_error('missing_requirements', 'Select at least one missing requirement or add a custom requirement.')
        cleaned_data['custom_requirements_list'] = custom_requirements
        return cleaned_data


class ProposalResubmissionForm(forms.Form):
    def __init__(self, *args, requirements=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.requirements = list(requirements or [])
        for requirement in self.requirements:
            if requirement.is_resubmitted:
                continue
            self.fields[f'requirement_{requirement.pk}'] = forms.FileField(
                label=requirement.label,
                required=True,
                widget=forms.FileInput(attrs={
                    'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
                })
            )
