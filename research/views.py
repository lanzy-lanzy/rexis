from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

from .models import ResearchRecord, ResearchStatus
from .forms import ResearchRecordForm
from proposals.models import Proposal, ProposalStatus, ProposalType
from users.models import UserRole


@login_required
def research_list(request: HttpRequest) -> HttpResponse:
    user = request.user
    records = ResearchRecord.objects.select_related('proposal', 'lead_researcher')

    if user.is_research_staff:
        records = records.filter(
            Q(lead_researcher=user) | Q(co_researchers=user)
        )
    elif user.is_faculty:
        records = records.filter(proposal__faculty_author=user)

    status_filter = request.GET.get('status')
    if status_filter:
        records = records.filter(status=status_filter)

    year_filter = request.GET.get('year')
    if year_filter:
        records = records.filter(publication_year=year_filter)

    # Get distinct years for the filter dropdown
    available_years = ResearchRecord.objects.filter(publication_year__isnull=False).values_list('publication_year', flat=True).distinct().order_by('-publication_year')

    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'research/research_list.html', {
        'page_obj': page_obj,
        'status_choices': ResearchStatus.choices,
        'available_years': available_years,
        'current_year_filter': year_filter,
    })


@login_required
def research_create(request: HttpRequest) -> HttpResponse:
    if not request.user.is_research_staff and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    approved_proposals = Proposal.objects.filter(
        proposal_type=ProposalType.RESEARCH,
        status=ProposalStatus.APPROVED
    )

    if request.method == 'POST':
        form = ResearchRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.lead_researcher = request.user
            record.save()
            form.save_m2m()
            messages.success(request, 'Research record created successfully!')
            return redirect('research_list')
    else:
        form = ResearchRecordForm()
        form.fields['proposal'].queryset = approved_proposals

    return render(request, 'research/research_form.html', {'form': form})


@login_required
def research_detail(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(ResearchRecord, pk=pk)
    return render(request, 'research/research_detail.html', {'record': record})


@login_required
def research_edit(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(ResearchRecord, pk=pk)
    
    if record.lead_researcher != request.user and not request.user.is_admin:
        messages.error(request, 'You can only edit your own research records.')
        return redirect('research_list')

    if request.method == 'POST':
        form = ResearchRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Research record updated successfully!')
            return redirect('research_detail', pk=record.pk)
    else:
        form = ResearchRecordForm(instance=record)

    return render(request, 'research/research_form.html', {'form': form, 'record': record})


@login_required
def faculty_proposal_abstracts(request: HttpRequest) -> HttpResponse:
    if not request.user.is_research_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    proposals = Proposal.objects.filter(
        proposal_type=ProposalType.RESEARCH,
        status=ProposalStatus.APPROVED
    ).select_related('faculty_author')

    search = request.GET.get('search')
    if search:
        proposals = proposals.filter(
            Q(title__icontains=search) | 
            Q(abstract__icontains=search) |
            Q(faculty_author__first_name__icontains=search) |
            Q(faculty_author__last_name__icontains=search)
        )

    paginator = Paginator(proposals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'research/faculty_abstracts.html', {'page_obj': page_obj})
