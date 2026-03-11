from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Proposal, ProposalStatus, ProposalType
from .forms import ProposalForm, ProposalReviewForm
from users.models import UserRole


@login_required
def proposal_list(request: HttpRequest) -> HttpResponse:
    user = request.user
    proposals = Proposal.objects.select_related('faculty_author', 'research_staff')

    if user.is_faculty:
        proposals = proposals.filter(faculty_author=user)
    elif user.is_research_staff:
        proposals = proposals.filter(
            Q(faculty_author=user) | Q(research_staff=user)
        )
    elif user.is_extension_staff:
        proposals = proposals.filter(proposal_type=ProposalType.EXTENSION)

    status_filter = request.GET.get('status')
    if status_filter:
        proposals = proposals.filter(status=status_filter)

    type_filter = request.GET.get('proposal_type')
    if type_filter:
        proposals = proposals.filter(proposal_type=type_filter)

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

    context = {
        'page_obj': page_obj,
        'status_choices': ProposalStatus.choices,
        'type_choices': ProposalType.choices,
    }
    return render(request, 'proposals/proposal_list.html', context)


@login_required
def proposal_create(request: HttpRequest) -> HttpResponse:
    if not request.user.is_faculty:
        messages.error(request, 'Only faculty members can submit proposals.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.faculty_author = request.user
            proposal.save()
            messages.success(request, 'Proposal submitted successfully!')
            if request.htmx:
                return render(request, 'proposals/partials/proposal_success.html', {'proposal': proposal})
            return redirect('proposal_list')
    else:
        form = ProposalForm()

    if request.htmx:
        return render(request, 'proposals/partials/proposal_form.html', {'form': form})

    return render(request, 'proposals/proposal_form.html', {'form': form})


@login_required
def proposal_detail(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)
    user = request.user

    if user.is_research_staff:
        return render(request, 'proposals/proposal_research_detail.html', {'proposal': proposal})

    return render(request, 'proposals/proposal_detail.html', {'proposal': proposal})


@login_required
def proposal_edit(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)
    
    if proposal.faculty_author != request.user:
        messages.error(request, 'You can only edit your own proposals.')
        return redirect('proposal_list')

    if proposal.status != ProposalStatus.PENDING:
        messages.error(request, 'You can only edit pending proposals.')
        return redirect('proposal_list')

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES, instance=proposal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proposal updated successfully!')
            return redirect('proposal_detail', pk=proposal.pk)
    else:
        form = ProposalForm(instance=proposal)

    return render(request, 'proposals/proposal_form.html', {'form': form, 'proposal': proposal})


@login_required
def proposal_review(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)
    
    if not request.user.is_admin:
        messages.error(request, 'Only administrators can review proposals.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProposalReviewForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.reviewed_by = request.user
            proposal.reviewed_at = timezone.now()
            proposal.save()
            messages.success(request, f'Proposal {proposal.get_status_display()}!')
            return redirect('proposal_list')
    else:
        form = ProposalReviewForm(instance=proposal)

    return render(request, 'proposals/proposal_review.html', {'form': form, 'proposal': proposal})


@login_required
def proposal_htmx_list(request: HttpRequest) -> HttpResponse:
    user = request.user
    proposals = Proposal.objects.select_related('faculty_author')

    if user.is_faculty:
        proposals = proposals.filter(faculty_author=user)
    elif user.is_research_staff:
        proposals = proposals.filter(research_staff=user)

    status_filter = request.GET.get('status')
    if status_filter:
        proposals = proposals.filter(status=status_filter)

    search = request.GET.get('search')
    if search:
        proposals = proposals.filter(title__icontains=search)

    proposals = proposals[:10]
    return render(request, 'proposals/partials/proposal_rows.html', {'proposals': proposals})


def validate_proposal(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        abstract = request.POST.get('abstract', '').strip()
        
        errors = {}
        if len(title) < 10:
            errors['title'] = 'Title must be at least 10 characters.'
        if len(abstract) < 50:
            errors['abstract'] = 'Abstract must be at least 50 characters.'
        
        if request.htmx:
            if errors:
                return JsonResponse({'valid': False, 'errors': errors}, status=400)
            return JsonResponse({'valid': True})
        
        if errors:
            for error in errors.values():
                messages.error(request, error)
            return redirect('proposal_create')
    
    return JsonResponse({'valid': False}, status=400)
