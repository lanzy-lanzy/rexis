from django.contrib import admin
from .models import Proposal


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'faculty_author', 'proposal_type', 'status', 'date_submitted')
    list_filter = ('status', 'proposal_type', 'date_submitted')
    search_fields = ('title', 'abstract', 'faculty_author__username')
    date_hierarchy = 'date_submitted'
    readonly_fields = ('date_submitted', 'date_updated')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'abstract', 'full_description', 'proposal_type')
        }),
        ('Authors', {
            'fields': ('faculty_author', 'research_staff')
        }),
        ('Documents', {
            'fields': ('proposal_document', 'budget_pdf', 'supporting_image')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('date_submitted', 'date_updated'),
            'classes': ('collapse',)
        }),
    )
