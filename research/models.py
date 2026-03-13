from django.db import models
from django.conf import settings
from proposals.models import Proposal


class ResearchStatus(models.TextChoices):
    ONGOING = 'ONGOING', 'Ongoing'
    COMPLETED = 'COMPLETED', 'Completed'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    PUBLISHED = 'PUBLISHED', 'Published'


class ResearchRecord(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='research_records'
    )
    lead_researcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='research_lead'
    )
    co_researchers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='research_coauthored',
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=ResearchStatus.choices,
        default=ResearchStatus.ONGOING
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    funding_source = models.CharField(max_length=255, blank=True)
    funding_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    output_description = models.TextField(blank=True)
    publication_link = models.URLField(blank=True)
    publication_year = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="The year this research was officially published"
    )
    citation_count = models.PositiveIntegerField(
        default=0, 
        help_text="Number of times this research has been cited"
    )
    citations_list = models.TextField(
        blank=True, 
        help_text="List of sources that cited this research (APA/MLA format)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Research Record'
        verbose_name_plural = 'Research Records'

    def __str__(self):
        return f"Research: {self.proposal.title}"
