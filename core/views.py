from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from research.models import ResearchRecord
from extension.models import ExtensionRecord
from users.models import CustomUser, UserRole
from proposals.models import Proposal
from .reports import build_report_pdf, get_report_context

def home(request):
    research_count = ResearchRecord.objects.count()
    extension_count = ExtensionRecord.objects.count()
    faculty_count = CustomUser.objects.filter(role=UserRole.FACULTY).count()
    
    # Get unique partner communities
    communities_count = ExtensionRecord.objects.exclude(partner_community='').values('partner_community').distinct().count()

    context = {
        'research_count': research_count,
        'extension_count': extension_count,
        'faculty_count': faculty_count,
        'communities_count': communities_count,
    }
    return render(request, 'home.html', context)


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'proposals': [],
        'research': [],
        'extensions': [],
        'users': [],
    }

    if query:
        # Search Proposals
        results['proposals'] = Proposal.objects.filter(
            Q(title__icontains=query) |
            Q(abstract__icontains=query) |
            Q(faculty_author__first_name__icontains=query) |
            Q(faculty_author__last_name__icontains=query)
        ).select_related('faculty_author')[:15]

        # Search Research Records
        results['research'] = ResearchRecord.objects.filter(
            Q(proposal__title__icontains=query) |
            Q(lead_researcher__first_name__icontains=query) |
            Q(lead_researcher__last_name__icontains=query) |
            Q(funding_source__icontains=query) |
            Q(output_description__icontains=query)
        ).select_related('proposal', 'lead_researcher')[:15]

        # Search Extension Records
        results['extensions'] = ExtensionRecord.objects.filter(
            Q(title__icontains=query) |
            Q(partner_community__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query) |
            Q(coordinator__first_name__icontains=query) |
            Q(coordinator__last_name__icontains=query)
        ).select_related('coordinator')[:15]

        # Search Users
        results['users'] = CustomUser.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(department__icontains=query) |
            Q(employee_id__icontains=query)
        )[:10]

    total_count = sum(len(v) for v in results.values())

    context = {
        'query': query,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'core/search_results.html', context)


@login_required
def comprehensive_reports(request):
    context = get_report_context(request.user, request.GET)
    return render(request, 'core/comprehensive_reports.html', context)


@login_required
def comprehensive_reports_pdf(request):
    context = get_report_context(request.user, request.GET)
    pdf = build_report_pdf(context, request.user)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="comprehensive-report.pdf"'
    return response
