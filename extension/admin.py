from django.contrib import admin
from .models import ExtensionRecord


@admin.register(ExtensionRecord)
class ExtensionRecordAdmin(admin.ModelAdmin):
    list_display = ('title', 'extension_type', 'coordinator', 'status', 'start_date', 'beneficiary_count')
    list_filter = ('status', 'extension_type', 'start_date')
    search_fields = ('title', 'coordinator__username', 'partner_community')
    date_hierarchy = 'start_date'
    filter_horizontal = ('team_members',)
