from django.db import models
from django.conf import settings


class ProposalStatus(models.TextChoices):
    PENDING_RECOMMENDATION = 'PENDING_RECOMMENDATION', 'Pending Staff Recommendation'
    RECOMMENDED_APPROVAL = 'RECOMMENDED_APPROVAL', 'Recommended for Admin Approval'
    RECOMMENDED_REVISION = 'RECOMMENDED_REVISION', 'Recommended for Revision'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'


class ProjectProgressStatus(models.TextChoices):
    ONGOING = 'ONGOING', 'Ongoing'
    PRESENTED = 'PRESENTED', 'Presented'
    COMPLETED = 'COMPLETED', 'Completed'
    PUBLISHED = 'PUBLISHED', 'Published'


class ProposalType(models.TextChoices):
    RESEARCH = 'RESEARCH', 'Research'
    EXTENSION = 'EXTENSION', 'Extension'


class ProposalTrackingEventType(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted'
    DOCUMENTS_UPLOADED = 'DOCUMENTS_UPLOADED', 'Documents Uploaded'
    RECOMMENDED_APPROVAL = 'RECOMMENDED_APPROVAL', 'Recommended for Approval'
    REVISION_REQUESTED = 'REVISION_REQUESTED', 'Revision Requested'
    ADMIN_APPROVED = 'ADMIN_APPROVED', 'Approved by Admin'
    ADMIN_REJECTED = 'ADMIN_REJECTED', 'Rejected by Admin'
    RESUBMITTED = 'RESUBMITTED', 'Resubmitted'
    UPDATED = 'UPDATED', 'Updated'


PROPOSAL_REQUIREMENT_CHOICES = [
    ('proposal_document', 'Proposal Document'),
    ('budget_pdf', 'Budget Letter or Budget PDF'),
    ('workplan', 'Workplan'),
    ('moa', 'MOA'),
    ('supporting_image', 'Supporting Image or Evidence'),
]

PROPOSAL_REQUIREMENT_LABELS = dict(PROPOSAL_REQUIREMENT_CHOICES)
PROPOSAL_REQUIREMENT_MAPPED_FIELDS = {
    'proposal_document': 'proposal_document',
    'budget_pdf': 'budget_pdf',
    'supporting_image': 'supporting_image',
}


class Proposal(models.Model):
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    full_description = models.TextField()
    proposal_type = models.CharField(
        max_length=20,
        choices=ProposalType.choices,
        default=ProposalType.RESEARCH
    )
    faculty_author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='proposals_authored'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_submitted'
    )
    submitted_on_behalf = models.BooleanField(default=False)
    research_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_research'
    )
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    proposal_document = models.FileField(upload_to='proposals/documents/', blank=True, null=True)
    budget_pdf = models.FileField(upload_to='proposals/budgets/', blank=True, null=True)
    supporting_image = models.ImageField(upload_to='proposals/images/', blank=True, null=True)
    status = models.CharField(
        max_length=30,
        choices=ProposalStatus.choices,
        default=ProposalStatus.PENDING_RECOMMENDATION
    )
    recommended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_recommended'
    )
    recommendation_notes = models.TextField(blank=True)
    recommended_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_reviewed'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    project_progress_status = models.CharField(
        max_length=20,
        choices=ProjectProgressStatus.choices,
        blank=True
    )
    progress_report = models.FileField(upload_to='proposals/progress_reports/', blank=True, null=True)
    abstract_document = models.FileField(upload_to='proposals/abstracts/', blank=True, null=True)
    certificate_of_appearance = models.FileField(upload_to='proposals/certificates/', blank=True, null=True)
    certificate_of_participation = models.FileField(upload_to='proposals/certificates/', blank=True, null=True)
    conference_proceedings = models.FileField(upload_to='proposals/proceedings/', blank=True, null=True)
    full_paper = models.FileField(upload_to='proposals/full_papers/', blank=True, null=True)
    certificate_of_publication = models.FileField(upload_to='proposals/certificates/', blank=True, null=True)

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Proposal'
        verbose_name_plural = 'Proposals'

    def __str__(self):
        return self.title


class ProposalDocumentVersion(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='document_versions'
    )
    document = models.FileField(upload_to='proposals/documents/versions/')
    version_number = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    version_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-version_number']
        verbose_name = 'Proposal Document Version'
        verbose_name_plural = 'Proposal Document Versions'

    def __str__(self):
        return f"{self.proposal.title} - v{self.version_number}"


class ProposalRequirement(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='requirements'
    )
    requirement_key = models.CharField(max_length=100)
    label = models.CharField(max_length=255)
    is_custom = models.BooleanField(default=False)
    uploaded_file = models.FileField(upload_to='proposals/requirements/', blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    is_resubmitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name = 'Proposal Requirement'
        verbose_name_plural = 'Proposal Requirements'

    def __str__(self):
        return f"{self.proposal.title} - {self.label}"


class ProposalTrackingEvent(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='tracking_events'
    )
    event_type = models.CharField(
        max_length=40,
        choices=ProposalTrackingEventType.choices
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=ProposalStatus.choices,
        blank=True
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal_tracking_events'
    )
    document_label = models.CharField(max_length=255, blank=True)
    document_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Proposal Tracking Event'
        verbose_name_plural = 'Proposal Tracking Events'

    def __str__(self):
        return f"{self.proposal.title} - {self.title}"
