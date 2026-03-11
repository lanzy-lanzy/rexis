from django.db import models
from django.conf import settings


class ProposalStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'


class ProposalType(models.TextChoices):
    RESEARCH = 'RESEARCH', 'Research'
    EXTENSION = 'EXTENSION', 'Extension'


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
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_reviewed'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

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
