from django.contrib import admin
from .models import ResearchRecord


@admin.register(ResearchRecord)
class ResearchRecordAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'lead_researcher', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date')
    search_fields = ('proposal__title', 'lead_researcher__username')
    date_hierarchy = 'start_date'
    filter_horizontal = ('co_researchers',)
