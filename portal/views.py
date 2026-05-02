from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.db.models import Count, Q

from proposals.models import Proposal, ProposalStatus, ProposalType
from research.models import ResearchRecord, ResearchStatus
from extension.models import ExtensionRecord, ExtensionStatus
from users.models import CustomUser, UserRole


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user

    if user.is_admin:
        return admin_dashboard(request)
    elif user.is_faculty:
        return faculty_dashboard(request)
    elif user.is_research_extension_staff:
        return research_extension_dashboard(request)

    return redirect('login')


def admin_dashboard(request: HttpRequest) -> HttpResponse:
    total_proposals = Proposal.objects.count()
    pending_recommendations = Proposal.objects.filter(status=ProposalStatus.PENDING_RECOMMENDATION).count()
    recommended_approval = Proposal.objects.filter(status=ProposalStatus.RECOMMENDED_APPROVAL).count()
    approved_proposals = Proposal.objects.filter(status=ProposalStatus.APPROVED).count()
    rejected_proposals = Proposal.objects.filter(status=ProposalStatus.REJECTED).count()

    research_proposals = Proposal.objects.filter(proposal_type=ProposalType.RESEARCH).count()
    extension_proposals = Proposal.objects.filter(proposal_type=ProposalType.EXTENSION).count()

    total_research = ResearchRecord.objects.count()
    ongoing_research = ResearchRecord.objects.filter(status=ResearchStatus.ONGOING).count()

    total_extension = ExtensionRecord.objects.count()
    ongoing_extension = ExtensionRecord.objects.filter(status=ExtensionStatus.ONGOING).count()

    total_users = CustomUser.objects.count()
    faculty_count = CustomUser.objects.filter(role=UserRole.FACULTY).count()
    staff_count = CustomUser.objects.filter(role=UserRole.RESEARCH_EXTENSION_STAFF).count()
    
    recent_proposals = Proposal.objects.select_related('faculty_author')[:5]
    recent_research = ResearchRecord.objects.select_related('proposal', 'lead_researcher')[:5]
    recent_extension = ExtensionRecord.objects.select_related('coordinator')[:5]
    
    context = {
        'total_proposals': total_proposals,
        'pending_proposals': pending_recommendations,
        'approved_proposals': approved_proposals,
        'rejected_proposals': rejected_proposals,
        'research_proposals': research_proposals,
        'extension_proposals': extension_proposals,
        'total_research': total_research,
        'ongoing_research': ongoing_research,
        'total_extension': total_extension,
        'ongoing_extension': ongoing_extension,
        'total_users': total_users,
        'faculty_count': faculty_count,
        'research_count': staff_count,
        'extension_count': staff_count,
        'recent_proposals': recent_proposals,
        'recent_research': recent_research,
        'recent_extension': recent_extension,
    }
    return render(request, 'portal/admin_dashboard.html', context)


def research_extension_dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user
    pending_recommendations = Proposal.objects.filter(status=ProposalStatus.PENDING_RECOMMENDATION)
    recommended_for_admin = Proposal.objects.filter(status=ProposalStatus.RECOMMENDED_APPROVAL)
    ongoing_projects = Proposal.objects.filter(
        status=ProposalStatus.APPROVED,
        project_progress_status='ONGOING',
    )
    presented_projects = Proposal.objects.filter(
        status=ProposalStatus.APPROVED,
        project_progress_status='PRESENTED',
    )
    completed_projects = Proposal.objects.filter(
        status=ProposalStatus.APPROVED,
        project_progress_status='COMPLETED',
    )

    context = {
        'pending_recommendations': pending_recommendations[:5],
        'recommended_for_admin': recommended_for_admin[:5],
        'total_pending_recommendations': pending_recommendations.count(),
        'total_recommended_for_admin': recommended_for_admin.count(),
        'ongoing_projects': ongoing_projects.count(),
        'presented_projects': presented_projects.count(),
        'completed_projects': completed_projects.count(),
        'my_submitted_proposals': Proposal.objects.filter(submitted_by=user)[:5],
    }
    return render(request, 'portal/research_extension_dashboard.html', context)


def faculty_dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user

    my_proposals = Proposal.objects.filter(faculty_author=user)
    pending_proposals = my_proposals.filter(
        status__in=[ProposalStatus.PENDING_RECOMMENDATION, ProposalStatus.RECOMMENDED_REVISION]
    ).count()
    approved_proposals = my_proposals.filter(status=ProposalStatus.APPROVED).count()
    rejected_proposals = my_proposals.filter(status=ProposalStatus.REJECTED).count()
    
    my_research = ResearchRecord.objects.filter(
        Q(lead_researcher=user) | Q(co_researchers=user)
    ).count()
    
    context = {
        'my_proposals': my_proposals[:5],
        'total_proposals': my_proposals.count(),
        'pending_proposals': pending_proposals,
        'approved_proposals': approved_proposals,
        'rejected_proposals': rejected_proposals,
        'my_research': my_research,
    }
    return render(request, 'portal/faculty_dashboard.html', context)


def research_dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user
    
    my_research = ResearchRecord.objects.filter(
        Q(lead_researcher=user) | Q(co_researchers=user)
    )
    ongoing_research = my_research.filter(status=ResearchStatus.ONGOING).count()
    completed_research = my_research.filter(status=ResearchStatus.COMPLETED).count()
    published_research = my_research.filter(status=ResearchStatus.PUBLISHED).count()
    
    approved_proposals = Proposal.objects.filter(
        proposal_type=ProposalType.RESEARCH,
        status=ProposalStatus.APPROVED
    ).count()
    
    pending_proposals = Proposal.objects.filter(
        proposal_type=ProposalType.RESEARCH,
        status=ProposalStatus.PENDING
    ).count()
    
    context = {
        'my_research': my_research[:5],
        'total_research': my_research.count(),
        'ongoing_research': ongoing_research,
        'completed_research': completed_research,
        'published_research': published_research,
        'approved_proposals': approved_proposals,
        'pending_proposals': pending_proposals,
    }
    return render(request, 'portal/research_dashboard.html', context)


def extension_dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user
    
    my_extension = ExtensionRecord.objects.filter(
        Q(coordinator=user) | Q(team_members=user)
    )
    ongoing_extension = my_extension.filter(status=ExtensionStatus.ONGOING).count()
    completed_extension = my_extension.filter(status=ExtensionStatus.COMPLETED).count()
    planning_extension = my_extension.filter(status=ExtensionStatus.PLANNING).count()
    
    context = {
        'my_extension': my_extension[:5],
        'total_extension': my_extension.count(),
        'ongoing_extension': ongoing_extension,
        'completed_extension': completed_extension,
        'planning_extension': planning_extension,
    }
    return render(request, 'portal/extension_dashboard.html', context)


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')
