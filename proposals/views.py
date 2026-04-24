from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import (
    Proposal,
    ProposalStatus,
    ProposalType,
    ProposalDocumentVersion,
    ProposalRequirement,
    PROPOSAL_REQUIREMENT_CHOICES,
    PROPOSAL_REQUIREMENT_LABELS,
    PROPOSAL_REQUIREMENT_MAPPED_FIELDS,
)
from .forms import ProposalForm, ProposalReviewForm, ProposalResubmissionForm
from users.models import UserRole


@login_required
def proposal_list(request: HttpRequest) -> HttpResponse:
    user = request.user
    proposals = Proposal.objects.select_related('faculty_author', 'research_staff')

    if user.is_faculty:
        proposals = proposals.filter(faculty_author=user)
    elif user.is_research_staff:
        proposals = proposals.filter(
            Q(faculty_author=user) | 
            Q(research_staff=user) |
            Q(status=ProposalStatus.APPROVED)
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
            
            # Create initial document version if a document was uploaded
            if 'proposal_document' in request.FILES:
                ProposalDocumentVersion.objects.create(
                    proposal=proposal,
                    document=request.FILES['proposal_document'],
                    version_number=1,
                    uploaded_by=request.user,
                    version_notes="Initial submission."
                )
                
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
    document_versions = proposal.document_versions.order_by('-version_number')
    requirements = proposal.requirements.all()
    resubmission_form = None

    if (
        user.is_faculty and
        proposal.faculty_author == user and
        proposal.status == ProposalStatus.REJECTED
    ):
        resubmission_form = ProposalResubmissionForm(
            requirements=requirements.filter(is_resubmitted=False)
        )

    context = {
        'proposal': proposal,
        'document_versions': document_versions,
        'requirements': requirements,
        'resubmission_form': resubmission_form,
    }

    if user.is_research_staff:
        return render(request, 'proposals/proposal_research_detail.html', context)

    return render(request, 'proposals/proposal_detail.html', context)


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
            proposal = form.save()
            
            # Create a new version if a new document was explicitly uploaded
            if 'proposal_document' in request.FILES:
                latest_version = proposal.document_versions.order_by('-version_number').first()
                next_version_num = (latest_version.version_number + 1) if latest_version else 1
                ProposalDocumentVersion.objects.create(
                    proposal=proposal,
                    document=request.FILES['proposal_document'],
                    version_number=next_version_num,
                    uploaded_by=request.user,
                    version_notes="Updated document via proposal edit."
                )

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
            if proposal.status == ProposalStatus.REJECTED:
                proposal.requirements.all().delete()
                fixed_keys = form.cleaned_data.get('missing_requirements') or []
                fixed_order = [key for key, _label in PROPOSAL_REQUIREMENT_CHOICES if key in fixed_keys]
                for key in fixed_order:
                    ProposalRequirement.objects.create(
                        proposal=proposal,
                        requirement_key=key,
                        label=PROPOSAL_REQUIREMENT_LABELS[key],
                    )
                for index, label in enumerate(form.cleaned_data.get('custom_requirements_list') or [], start=1):
                    ProposalRequirement.objects.create(
                        proposal=proposal,
                        requirement_key=f'custom_{index}',
                        label=label,
                        is_custom=True,
                    )
            messages.success(request, f'Proposal {proposal.get_status_display()}!')
            return redirect('proposal_list')
    else:
        form = ProposalReviewForm(instance=proposal)

    return render(request, 'proposals/proposal_review.html', {
        'form': form,
        'proposal': proposal,
        'requirements': proposal.requirements.all(),
    })


@login_required
def proposal_resubmit(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)

    if proposal.faculty_author != request.user:
        messages.error(request, 'You can only resubmit your own proposals.')
        return redirect('proposal_list')

    if proposal.status != ProposalStatus.REJECTED:
        messages.error(request, 'Only rejected proposals can be resubmitted.')
        return redirect('proposal_detail', pk=proposal.pk)

    requirements = proposal.requirements.filter(is_resubmitted=False)

    if request.method == 'POST':
        form = ProposalResubmissionForm(request.POST, request.FILES, requirements=requirements)
        if form.is_valid():
            proposal_update_fields = ['status', 'reviewed_by', 'reviewed_at', 'date_updated']
            document_version_file = None

            for requirement in requirements:
                upload = form.cleaned_data.get(f'requirement_{requirement.pk}')
                if not upload:
                    continue

                requirement.uploaded_file = upload
                requirement.uploaded_at = timezone.now()
                requirement.is_resubmitted = True
                requirement.save()

                mapped_field = PROPOSAL_REQUIREMENT_MAPPED_FIELDS.get(requirement.requirement_key)
                if mapped_field:
                    setattr(proposal, mapped_field, requirement.uploaded_file)
                    proposal_update_fields.append(mapped_field)
                    if mapped_field == 'proposal_document':
                        document_version_file = requirement.uploaded_file

            proposal.status = ProposalStatus.PENDING
            proposal.reviewed_by = None
            proposal.reviewed_at = None
            proposal.save(update_fields=list(dict.fromkeys(proposal_update_fields)))

            if document_version_file:
                latest_version = proposal.document_versions.order_by('-version_number').first()
                next_version_num = (latest_version.version_number + 1) if latest_version else 1
                ProposalDocumentVersion.objects.create(
                    proposal=proposal,
                    document=document_version_file,
                    version_number=next_version_num,
                    uploaded_by=request.user,
                    version_notes="Resubmitted document for rejected proposal."
                )

            messages.success(request, 'Proposal resubmitted for review.')
            return redirect('proposal_detail', pk=proposal.pk)
    else:
        form = ProposalResubmissionForm(requirements=requirements)

    document_versions = proposal.document_versions.order_by('-version_number')
    return render(request, 'proposals/proposal_detail.html', {
        'proposal': proposal,
        'document_versions': document_versions,
        'requirements': proposal.requirements.all(),
        'resubmission_form': form,
    })


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
