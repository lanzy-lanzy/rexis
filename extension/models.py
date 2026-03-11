from django.db import models
from django.conf import settings
from proposals.models import Proposal


class ExtensionStatus(models.TextChoices):
    PLANNING = 'PLANNING', 'Planning'
    ONGOING = 'ONGOING', 'Ongoing'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class ExtensionType(models.TextChoices):
    TRAINING = 'TRAINING', 'Training'
    SEMINAR = 'SEMINAR', 'Seminar'
    WORKSHOP = 'WORKSHOP', 'Workshop'
    OUTREACH = 'OUTREACH', 'Outreach'
    COMMUNITY_SERVICE = 'COMMUNITY_SERVICE', 'Community Service'
    OTHER = 'OTHER', 'Other'


class ExtensionRecord(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='extension_records',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    extension_type = models.CharField(
        max_length=30,
        choices=ExtensionType.choices,
        default=ExtensionType.COMMUNITY_SERVICE
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extension_coordinated'
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='extension_participated',
        blank=True
    )
    partner_community = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=ExtensionStatus.choices,
        default=ExtensionStatus.PLANNING
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    beneficiary_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    output_documents = models.FileField(upload_to='extension/documents/', blank=True, null=True)
    photos = models.ImageField(upload_to='extension/photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Extension Record'
        verbose_name_plural = 'Extension Records'

    def __str__(self):
        return self.title
