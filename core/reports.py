from collections import Counter
from datetime import date
from io import BytesIO
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from extension.models import ExtensionRecord, NarrativeReport
from proposals.models import Proposal, ProposalType, ProposalStatus, ProjectProgressStatus
from research.models import ResearchRecord
from users.models import CustomUser


RECORD_TYPE_CHOICES = [
    ('all', 'All records'),
    ('proposal', 'Proposals'),
    ('research', 'Research records'),
    ('extension', 'Extension activities'),
    ('narrative', 'Narrative reports'),
]


def _status_rows(queryset, choices):
    counts = Counter(queryset.values_list('status', flat=True))
    return [
        {
            'label': label,
            'count': counts.get(value, 0),
        }
        for value, label in choices
    ]


def _currency(value):
    if value is None:
        return '0.00'
    return f'{value:,.2f}'


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _active_filters(params):
    params = params or {}
    record_type = params.get('record_type') or 'all'
    if record_type not in dict(RECORD_TYPE_CHOICES):
        record_type = 'all'

    return {
        'q': (params.get('q') or '').strip(),
        'record_type': record_type,
        'status': (params.get('status') or '').strip(),
        'start_date': (params.get('start_date') or '').strip(),
        'end_date': (params.get('end_date') or '').strip(),
        'approval_status': (params.get('approval_status') or '').strip(),
        'project_progress': (params.get('project_progress') or '').strip(),
        'department': (params.get('department') or '').strip(),
        'submitter_type': (params.get('submitter_type') or '').strip(),
    }


def _filter_querystring(filters):
    return urlencode({
        key: value
        for key, value in filters.items()
        if value and not (key == 'record_type' and value == 'all')
    })


def _combined_status_choices():
    seen = set()
    choices = []
    for model in (Proposal, ResearchRecord, ExtensionRecord):
        for value, label in model._meta.get_field('status').choices:
            if value not in seen:
                seen.add(value)
                choices.append((value, label))
    return choices


def _apply_status_filter(queryset, model, status):
    if not status:
        return queryset
    valid_statuses = {value for value, _label in model._meta.get_field('status').choices}
    if status not in valid_statuses:
        return queryset.none()
    return queryset.filter(status=status)


def get_report_context(user, params=None):
    filters = _active_filters(params)
    page = int(params.get('page', 1)) if params and params.get('page') else 1
    per_page = 10
    
    proposals = Proposal.objects.select_related('faculty_author')
    research_records = ResearchRecord.objects.select_related('proposal', 'lead_researcher')
    extension_records = ExtensionRecord.objects.select_related('proposal', 'coordinator')

    if user.is_admin:
        scope_label = 'Institution-wide'
        scope_description = 'All proposals, research records, extension activities, reports, and user totals.'
    elif user.is_faculty:
        scope_label = 'Faculty'
        scope_description = 'Records authored by you or where you are listed as a research or extension participant.'
        proposals = proposals.filter(faculty_author=user)
        research_records = research_records.filter(
            Q(proposal__faculty_author=user) | Q(lead_researcher=user) | Q(co_researchers=user)
        ).distinct()
        extension_records = extension_records.filter(
            Q(proposal__faculty_author=user) | Q(coordinator=user) | Q(team_members=user)
        ).distinct()
    elif user.is_research_extension_staff:
        scope_label = 'Research & Extension Staff'
        scope_description = 'Research and extension proposals awaiting recommendation and approved projects.'
        proposals = proposals.filter(
            Q(status=ProposalStatus.PENDING_RECOMMENDATION) |
            Q(status=ProposalStatus.RECOMMENDED_APPROVAL) |
            Q(submitted_by=user)
        )
        research_records = research_records.none()
        extension_records = extension_records.none()
    else:
        scope_label = 'User'
        scope_description = 'Records available to your account.'
        proposals = proposals.none()
        research_records = research_records.none()
        extension_records = extension_records.none()

    narrative_reports = NarrativeReport.objects.select_related(
        'extension_record',
        'submitted_by',
    ).filter(extension_record__in=extension_records)

    search = filters['q']
    if search:
        proposals = proposals.filter(
            Q(title__icontains=search) |
            Q(abstract__icontains=search) |
            Q(full_description__icontains=search) |
            Q(faculty_author__first_name__icontains=search) |
            Q(faculty_author__last_name__icontains=search) |
            Q(faculty_author__username__icontains=search)
        )
        research_records = research_records.filter(
            Q(proposal__title__icontains=search) |
            Q(lead_researcher__first_name__icontains=search) |
            Q(lead_researcher__last_name__icontains=search) |
            Q(lead_researcher__username__icontains=search) |
            Q(funding_source__icontains=search) |
            Q(output_description__icontains=search)
        )
        extension_records = extension_records.filter(
            Q(title__icontains=search) |
            Q(partner_community__icontains=search) |
            Q(location__icontains=search) |
            Q(description__icontains=search) |
            Q(coordinator__first_name__icontains=search) |
            Q(coordinator__last_name__icontains=search) |
            Q(coordinator__username__icontains=search)
        )
        narrative_reports = narrative_reports.filter(
            Q(extension_record__title__icontains=search) |
            Q(narrative__icontains=search) |
            Q(submitted_by__first_name__icontains=search) |
            Q(submitted_by__last_name__icontains=search) |
            Q(submitted_by__username__icontains=search)
        )

    proposals = _apply_status_filter(proposals, Proposal, filters['status'])
    research_records = _apply_status_filter(research_records, ResearchRecord, filters['status'])
    extension_records = _apply_status_filter(extension_records, ExtensionRecord, filters['status'])

    if filters['approval_status']:
        proposals = proposals.filter(status=filters['approval_status'])

    if filters['project_progress']:
        proposals = proposals.filter(project_progress_status=filters['project_progress'])

    if filters['department']:
        proposals = proposals.filter(faculty_author__department=filters['department'])

    if filters['submitter_type'] == 'faculty_direct':
        proposals = proposals.filter(submitted_on_behalf=False)
    elif filters['submitter_type'] == 'staff_on_behalf':
        proposals = proposals.filter(submitted_on_behalf=True)

    start_date = _parse_date(filters['start_date'])
    end_date = _parse_date(filters['end_date'])
    if start_date:
        proposals = proposals.filter(date_submitted__date__gte=start_date)
        research_records = research_records.filter(start_date__gte=start_date)
        extension_records = extension_records.filter(start_date__gte=start_date)
        narrative_reports = narrative_reports.filter(date_submitted__date__gte=start_date)
    if end_date:
        proposals = proposals.filter(date_submitted__date__lte=end_date)
        research_records = research_records.filter(start_date__lte=end_date)
        extension_records = extension_records.filter(start_date__lte=end_date)
        narrative_reports = narrative_reports.filter(date_submitted__date__lte=end_date)

    if filters['record_type'] == 'proposal':
        research_records = research_records.none()
        extension_records = extension_records.none()
        narrative_reports = narrative_reports.none()
    elif filters['record_type'] == 'research':
        proposals = proposals.none()
        extension_records = extension_records.none()
        narrative_reports = narrative_reports.none()
    elif filters['record_type'] == 'extension':
        proposals = proposals.none()
        research_records = research_records.none()
        narrative_reports = narrative_reports.none()
    elif filters['record_type'] == 'narrative':
        proposals = proposals.none()
        research_records = research_records.none()
        extension_records = extension_records.none()

    total_funding = research_records.aggregate(total=Sum('funding_amount'))['total']
    total_beneficiaries = extension_records.aggregate(total=Sum('beneficiary_count'))['total'] or 0

    proposals_paginator = Paginator(proposals, per_page)
    research_paginator = Paginator(research_records, per_page)
    extension_paginator = Paginator(extension_records, per_page)
    narrative_paginator = Paginator(narrative_reports, per_page)

    return {
        'generated_at': timezone.localtime(),
        'scope_label': scope_label,
        'scope_description': scope_description,
        'proposals': proposals_paginator.get_page(page),
        'research_records': research_paginator.get_page(page),
        'extension_records': extension_paginator.get_page(page),
        'narrative_reports': narrative_paginator.get_page(page),
        'proposals_paginator': proposals_paginator,
        'research_paginator': research_paginator,
        'extension_paginator': extension_paginator,
        'narrative_paginator': narrative_paginator,
        'total_proposals': proposals.count(),
        'total_research': research_records.count(),
        'total_extension': extension_records.count(),
        'total_reports': narrative_reports.count(),
        'total_funding': total_funding,
        'total_funding_display': _currency(total_funding),
        'total_beneficiaries': total_beneficiaries,
        'proposal_status_rows': _status_rows(proposals, Proposal._meta.get_field('status').choices),
        'research_status_rows': _status_rows(research_records, ResearchRecord._meta.get_field('status').choices),
        'extension_status_rows': _status_rows(extension_records, ExtensionRecord._meta.get_field('status').choices),
        'filters': filters,
        'filter_querystring': _filter_querystring(filters),
        'record_type_choices': RECORD_TYPE_CHOICES,
        'status_choices': _combined_status_choices(),
        'approval_status_choices': ProposalStatus.choices,
        'project_progress_choices': ProjectProgressStatus.choices,
        'department_choices': CustomUser.DEPARTMENT_CHOICES,
        'submitter_type_choices': [
            ('faculty_direct', 'Faculty Direct Submission'),
            ('staff_on_behalf', 'Staff on Behalf of Faculty'),
        ],
    }


def _name(user):
    if not user:
        return 'Unassigned'
    return user.get_full_name() or user.username


def _add_table(story, title, headings, rows, styles):
    story.append(Paragraph(title, styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    if not rows:
        story.append(Paragraph('No records found.', styles['BodyText']))
        story.append(Spacer(1, 0.2 * inch))
        return

    table = Table([headings] + rows, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))


def build_report_pdf(context, user):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph('Research & Extension (MIS) Comprehensive Report', styles['Title']),
        Paragraph(f"Scope: {context['scope_label']} | Generated for {_name(user)}", styles['BodyText']),
        Paragraph(f"Generated: {context['generated_at'].strftime('%B %d, %Y %I:%M %p')}", styles['BodyText']),
        Spacer(1, 0.2 * inch),
    ]

    summary_rows = [
        ['Proposals', context['total_proposals']],
        ['Research Records', context['total_research']],
        ['Extension Activities', context['total_extension']],
        ['Narrative Reports', context['total_reports']],
        ['Research Funding', f"PHP {context['total_funding_display']}"],
        ['Beneficiaries', context['total_beneficiaries']],
    ]
    _add_table(story, 'Summary', ['Metric', 'Value'], summary_rows, styles)

    proposal_rows = [
        [
            proposal.title,
            proposal.get_proposal_type_display(),
            proposal.get_status_display(),
            _name(proposal.faculty_author),
            proposal.date_submitted.strftime('%Y-%m-%d'),
        ]
        for proposal in context['proposals']
    ]
    _add_table(story, 'Proposals', ['Title', 'Type', 'Status', 'Faculty', 'Submitted'], proposal_rows, styles)

    research_rows = [
        [
            record.proposal.title,
            record.get_status_display(),
            _name(record.lead_researcher),
            record.start_date.strftime('%Y-%m-%d'),
            f"PHP {_currency(record.funding_amount)}",
        ]
        for record in context['research_records']
    ]
    _add_table(story, 'Research Records', ['Title', 'Status', 'Lead', 'Start', 'Funding'], research_rows, styles)

    extension_rows = [
        [
            record.title,
            record.get_status_display(),
            _name(record.coordinator),
            record.location,
            record.beneficiary_count,
        ]
        for record in context['extension_records']
    ]
    _add_table(story, 'Extension Activities', ['Title', 'Status', 'Coordinator', 'Location', 'Beneficiaries'], extension_rows, styles)

    report_rows = [
        [
            report.extension_record.title,
            report.get_quarter_display(),
            report.report_year,
            _name(report.submitted_by),
            report.date_submitted.strftime('%Y-%m-%d'),
        ]
        for report in context['narrative_reports']
    ]
    _add_table(story, 'Narrative Reports', ['Activity', 'Quarter', 'Year', 'Submitted By', 'Submitted'], report_rows, styles)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
