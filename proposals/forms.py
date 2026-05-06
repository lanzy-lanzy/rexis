from django import forms
from .models import Proposal, ProposalStatus, ProjectProgressStatus, PROPOSAL_REQUIREMENT_CHOICES
from users.models import CustomUser, UserRole


SUBMISSION_STATUS_CHOICES = [
    ('', 'Select status...'),
    (ProjectProgressStatus.ONGOING, 'Ongoing'),
    (ProjectProgressStatus.COMPLETED, 'Completed'),
    (ProjectProgressStatus.PRESENTED, 'Presented'),
    (ProjectProgressStatus.PUBLISHED, 'Published'),
]

REQUIRED_DOCUMENTS_BY_STATUS = {
    ProjectProgressStatus.ONGOING: ['proposal_document', 'budget_pdf'],
    ProjectProgressStatus.COMPLETED: ['progress_report'],
    ProjectProgressStatus.PRESENTED: [
        'certificate_of_appearance',
        'certificate_of_participation',
        'abstract_document',
        'conference_proceedings',
    ],
    ProjectProgressStatus.PUBLISHED: ['full_paper', 'certificate_of_publication'],
}

DOCUMENT_ERROR_LABELS = {
    'proposal_document': 'Proposal document',
    'budget_pdf': 'Budget file',
    'progress_report': 'Progress/terminal report',
    'certificate_of_appearance': 'Certificate of appearance',
    'certificate_of_participation': 'Certificate of participation',
    'abstract_document': 'Abstract document',
    'conference_proceedings': 'Conference proceedings',
    'full_paper': 'Full paper',
    'certificate_of_publication': 'Certificate of publication',
}


class ProposalForm(forms.ModelForm):
    project_status = forms.ChoiceField(
        choices=SUBMISSION_STATUS_CHOICES,
        required=True,
        label='Project Status',
        widget=forms.Select(attrs={
            'form': 'proposalForm',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white'
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if self.instance and self.instance.pk and not self.is_bound:
            self.fields['project_status'].initial = self.instance.project_progress_status

        for field in [
            'research_staff',
            'proposal_document',
            'budget_pdf',
            'progress_report',
            'abstract_document',
            'certificate_of_appearance',
            'certificate_of_participation',
            'conference_proceedings',
            'full_paper',
            'certificate_of_publication',
        ]:
            if field in self.fields:
                self.fields[field].required = False

        if 'full_description' in self.fields:
            self.fields['full_description'].required = False

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

        if user and user.is_faculty:
            for field in ['abstract', 'supporting_image']:
                if field in self.fields:
                    self.fields.pop(field)

    class Meta:
        model = Proposal
        fields = ['title', 'abstract', 'full_description', 'proposal_type',
                  'research_staff', 'proposal_document', 'budget_pdf', 'supporting_image', 'faculty_author',
                  'progress_report', 'abstract_document', 'certificate_of_appearance', 'certificate_of_participation', 'conference_proceedings',
                  'full_paper', 'certificate_of_publication']
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
            'project_status': forms.Select(attrs={
                'form': 'proposalForm',
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
            'progress_report': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100'
            }),
            'abstract_document': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-cyan-50 file:text-cyan-700 hover:file:bg-cyan-100'
            }),
            'certificate_of_appearance': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-cyan-50 file:text-cyan-700 hover:file:bg-cyan-100'
            }),
            'certificate_of_participation': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            }),
            'conference_proceedings': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100'
            }),
            'full_paper': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-rose-50 file:text-rose-700 hover:file:bg-rose-100'
            }),
            'certificate_of_publication': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        project_status = cleaned_data.get('project_status')
        title = (cleaned_data.get('title') or '').strip()

        if title and len(title) < 10:
            self.add_error('title', 'Title must be at least 10 characters.')

        if project_status == ProjectProgressStatus.ONGOING and not (cleaned_data.get('full_description') or '').strip():
            self.add_error('full_description', 'Full description is required for Ongoing status.')

        if project_status != ProjectProgressStatus.ONGOING:
            cleaned_data['full_description'] = cleaned_data.get('full_description') or ''

        for field in REQUIRED_DOCUMENTS_BY_STATUS.get(project_status, []):
            if field in self.fields and not self._has_file(field, cleaned_data):
                label = DOCUMENT_ERROR_LABELS.get(field, self.fields[field].label or field.replace('_', ' ').title())
                self.add_error(field, f'{label} is required for {ProjectProgressStatus(project_status).label} status.')

        return cleaned_data

    def _has_file(self, field, cleaned_data):
        uploaded_file = cleaned_data.get(field)
        if uploaded_file:
            return True
        if self.instance and self.instance.pk:
            return bool(getattr(self.instance, field, None))
        return False

    def save(self, commit=True):
        proposal = super().save(commit=False)
        proposal.project_progress_status = self.cleaned_data.get('project_status', '')
        if commit:
            proposal.save()
        return proposal


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
