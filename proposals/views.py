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
    ProjectProgressStatus,
    ProposalTrackingEvent,
    ProposalTrackingEventType,
    ProposalDocumentVersion,
    ProposalRequirement,
    PROPOSAL_REQUIREMENT_CHOICES,
    PROPOSAL_REQUIREMENT_LABELS,
    PROPOSAL_REQUIREMENT_MAPPED_FIELDS,
)
from .forms import (
    DOCUMENT_ERROR_LABELS,
    ProposalForm,
    ProposalRecommendationForm,
    ProposalReviewForm,
    ProposalResubmissionForm,
    REQUIRED_DOCUMENTS_BY_STATUS,
)
from users.models import CustomUser, UserRole


TRACKED_DOCUMENT_FIELDS = {
    'proposal_document': 'Proposal Document',
    'budget_pdf': 'Budget PDF',
    'supporting_image': 'Supporting Image',
    'progress_report': 'Progress/Terminal Report',
    'abstract_document': 'Abstract Document',
    'certificate_of_appearance': 'Certificate of Appearance',
    'certificate_of_participation': 'Certificate of Participation',
    'conference_proceedings': 'Conference Proceedings',
    'full_paper': 'Full Paper',
    'certificate_of_publication': 'Certificate of Publication',
}


HISTORICAL_PROGRESS_STATUSES = {
    ProjectProgressStatus.PRESENTED,
    ProjectProgressStatus.COMPLETED,
    ProjectProgressStatus.PUBLISHED,
}


def visible_proposals_for_user(user):
    proposals = Proposal.objects.select_related('faculty_author', 'research_staff', 'submitted_by')

    if user.is_faculty:
        return proposals.filter(faculty_author=user)
    if user.is_research_extension_staff:
        return proposals.filter(
            Q(status=ProposalStatus.PENDING_RECOMMENDATION) |
            Q(status=ProposalStatus.RECOMMENDED_APPROVAL) |
            Q(status=ProposalStatus.RECOMMENDED_REVISION) |
            Q(status=ProposalStatus.APPROVED) |
            Q(submitted_by=user)
        )
    return proposals


def proposal_document_statuses(proposal):
    required_fields = set(REQUIRED_DOCUMENTS_BY_STATUS.get(proposal.project_progress_status, []))
    statuses = []

    for field, default_label in TRACKED_DOCUMENT_FIELDS.items():
        file_field = getattr(proposal, field, None)
        uploaded = bool(file_field)
        required = field in required_fields
        label = DOCUMENT_ERROR_LABELS.get(field, default_label)

        if uploaded:
            state = 'uploaded'
            state_label = 'Uploaded'
        elif required:
            state = 'missing'
            state_label = 'Missing'
        else:
            state = 'optional'
            state_label = 'Optional'

        statuses.append({
            'field': field,
            'label': label,
            'required': required,
            'uploaded': uploaded,
            'state': state,
            'state_label': state_label,
            'file': file_field,
        })

    for requirement in proposal.requirements.all():
        uploaded = bool(requirement.uploaded_file)
        statuses.append({
            'field': f'requirement_{requirement.pk}',
            'label': requirement.label,
            'required': True,
            'uploaded': uploaded,
            'state': 'uploaded' if uploaded else 'missing',
            'state_label': 'Uploaded' if uploaded else 'Missing',
            'file': requirement.uploaded_file,
        })

    return statuses


def proposal_detail_context(proposal, **extra):
    context = {
        'proposal': proposal,
        'document_versions': proposal.document_versions.order_by('-version_number'),
        'requirements': proposal.requirements.all(),
        'document_statuses': proposal_document_statuses(proposal),
        'tracking_events': proposal.tracking_events.select_related('actor'),
        'show_submission_narrative': proposal.project_progress_status not in HISTORICAL_PROGRESS_STATUSES,
    }
    context.update(extra)
    return context


def log_proposal_event(
    proposal,
    event_type,
    title,
    actor=None,
    description='',
    status='',
    document_label='',
    document_url='',
):
    return ProposalTrackingEvent.objects.create(
        proposal=proposal,
        event_type=event_type,
        title=title,
        description=description,
        status=status or proposal.status,
        actor=actor,
        document_label=document_label,
        document_url=document_url,
    )


def uploaded_document_labels(files):
    return [
        label
        for field, label in TRACKED_DOCUMENT_FIELDS.items()
        if field in files
    ]


def replace_proposal_requirements(proposal, fixed_keys, custom_labels):
    proposal.requirements.all().delete()
    fixed_order = [key for key, _label in PROPOSAL_REQUIREMENT_CHOICES if key in fixed_keys]
    for key in fixed_order:
        ProposalRequirement.objects.create(
            proposal=proposal,
            requirement_key=key,
            label=PROPOSAL_REQUIREMENT_LABELS[key],
        )
    for index, label in enumerate(custom_labels or [], start=1):
        ProposalRequirement.objects.create(
            proposal=proposal,
            requirement_key=f'custom_{index}',
            label=label,
            is_custom=True,
        )


@login_required
def proposal_list(request: HttpRequest) -> HttpResponse:
    proposals = visible_proposals_for_user(request.user)

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
def proposal_tracking_dashboard(request: HttpRequest) -> HttpResponse:
    proposals = visible_proposals_for_user(request.user).prefetch_related('tracking_events', 'requirements')

    search = (request.GET.get('search') or '').strip()
    if search:
        document_filters = Q()
        for field in TRACKED_DOCUMENT_FIELDS:
            document_filters |= Q(**{f'{field}__icontains': search})

        proposals = proposals.filter(
            Q(title__icontains=search) |
            Q(abstract__icontains=search) |
            Q(faculty_author__first_name__icontains=search) |
            Q(faculty_author__last_name__icontains=search) |
            Q(faculty_author__username__icontains=search) |
            document_filters
        )

    status_filter = request.GET.get('status')
    if status_filter:
        proposals = proposals.filter(status=status_filter)

    proposal_type_filter = request.GET.get('proposal_type')
    if proposal_type_filter:
        proposals = proposals.filter(proposal_type=proposal_type_filter)

    document_status_filter = request.GET.get('document_status')
    proposal_cards = []
    for proposal in proposals:
        documents = proposal_document_statuses(proposal)
        required_documents = [document for document in documents if document['required']]
        missing_documents = [document for document in required_documents if not document['uploaded']]

        if document_status_filter == 'complete' and missing_documents:
            continue
        if document_status_filter == 'missing' and not missing_documents:
            continue

        tracking_events = list(proposal.tracking_events.all())
        proposal_cards.append({
            'proposal': proposal,
            'documents': documents,
            'required_count': len(required_documents),
            'uploaded_required_count': len(required_documents) - len(missing_documents),
            'missing_count': len(missing_documents),
            'latest_events': tracking_events[:3],
            'latest_event': tracking_events[0] if tracking_events else None,
        })

    paginator = Paginator(proposal_cards, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'proposals/proposal_tracking_dashboard.html', {
        'page_obj': page_obj,
        'status_choices': ProposalStatus.choices,
        'type_choices': ProposalType.choices,
        'document_status': document_status_filter,
    })


@login_required
def proposal_create(request: HttpRequest) -> HttpResponse:
    if not (request.user.is_faculty or request.user.is_research_extension_staff):
        messages.error(request, 'Only faculty members or Research & Extension Staff can submit proposals.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            proposal = form.save(commit=False)
            if request.user.is_research_extension_staff:
                proposal.faculty_author = form.cleaned_data['faculty_author']
                proposal.submitted_by = request.user
                proposal.submitted_on_behalf = True
            else:
                proposal.faculty_author = request.user
                proposal.submitted_by = request.user
                proposal.submitted_on_behalf = False
            proposal.status = ProposalStatus.PENDING_RECOMMENDATION
            proposal.save()
            log_proposal_event(
                proposal,
                ProposalTrackingEventType.SUBMITTED,
                'Proposal submitted',
                actor=request.user,
                description='Proposal was submitted for Research & Extension staff recommendation.',
                status=proposal.status,
            )

            # Create initial document version if a document was uploaded
            if 'proposal_document' in request.FILES:
                ProposalDocumentVersion.objects.create(
                    proposal=proposal,
                    document=request.FILES['proposal_document'],
                    version_number=1,
                    uploaded_by=request.user,
                    version_notes="Initial submission."
                )
            document_labels = uploaded_document_labels(request.FILES)
            if document_labels:
                log_proposal_event(
                    proposal,
                    ProposalTrackingEventType.DOCUMENTS_UPLOADED,
                    'Submission documents uploaded',
                    actor=request.user,
                    description=', '.join(document_labels),
                    status=proposal.status,
                )

            messages.success(request, 'Proposal submitted successfully!')
            if request.htmx:
                return render(request, 'proposals/partials/proposal_success.html', {'proposal': proposal})
            return redirect('proposal_list')
        messages.error(request, 'Please correct the highlighted errors and submit the proposal again.')
    else:
        form = ProposalForm(user=request.user)

    if request.htmx:
        return render(request, 'proposals/partials/proposal_form.html', {'form': form})

    return render(request, 'proposals/proposal_form.html', {'form': form})


@login_required
def proposal_detail(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)
    user = request.user
    requirements = proposal.requirements.all()
    resubmission_form = None

    if (
        user.is_faculty and
        proposal.faculty_author == user and
        proposal.status in [ProposalStatus.REJECTED, ProposalStatus.RECOMMENDED_REVISION]
    ):
        resubmission_form = ProposalResubmissionForm(
            requirements=requirements.filter(is_resubmitted=False)
        )

    context = proposal_detail_context(proposal, resubmission_form=resubmission_form)

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
        form = ProposalForm(request.POST, request.FILES, instance=proposal, user=request.user)
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
            document_labels = uploaded_document_labels(request.FILES)
            log_proposal_event(
                proposal,
                ProposalTrackingEventType.UPDATED,
                'Proposal updated',
                actor=request.user,
                description=(
                    f"Updated documents: {', '.join(document_labels)}"
                    if document_labels
                    else 'Proposal details were updated.'
                ),
                status=proposal.status,
            )

            messages.success(request, 'Proposal updated successfully!')
            return redirect('proposal_detail', pk=proposal.pk)
        messages.error(request, 'Please correct the highlighted errors and save again.')
    else:
        form = ProposalForm(instance=proposal, user=request.user)

    return render(request, 'proposals/proposal_form.html', {'form': form, 'proposal': proposal})


@login_required
def proposal_recommend(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)

    if not request.user.is_research_extension_staff:
        messages.error(request, 'Only Research & Extension Staff can recommend proposals.')
        return redirect('dashboard')

    if proposal.status != ProposalStatus.PENDING_RECOMMENDATION:
        messages.error(request, 'Only proposals waiting for staff recommendation can be reviewed here.')
        return redirect('proposal_detail', pk=proposal.pk)

    if request.method == 'POST':
        form = ProposalRecommendationForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.recommended_by = request.user
            proposal.recommended_at = timezone.now()
            proposal.reviewed_by = None
            proposal.reviewed_at = None
            proposal.save()
            if proposal.status == ProposalStatus.RECOMMENDED_REVISION:
                replace_proposal_requirements(
                    proposal,
                    form.cleaned_data.get('missing_requirements') or [],
                    form.cleaned_data.get('custom_requirements_list') or [],
                )
                log_proposal_event(
                    proposal,
                    ProposalTrackingEventType.REVISION_REQUESTED,
                    'Revision requested by Research & Extension Staff',
                    actor=request.user,
                    description=form.cleaned_data.get('recommendation_notes') or 'Additional proposal requirements were requested.',
                    status=proposal.status,
                )
            elif proposal.status == ProposalStatus.RECOMMENDED_APPROVAL:
                proposal.requirements.filter(is_resubmitted=False).delete()
                log_proposal_event(
                    proposal,
                    ProposalTrackingEventType.RECOMMENDED_APPROVAL,
                    'Recommended for admin approval',
                    actor=request.user,
                    description=form.cleaned_data.get('recommendation_notes') or 'Proposal was recommended for administrator approval.',
                    status=proposal.status,
                )
            messages.success(request, 'Proposal recommendation submitted.')
            return redirect('proposal_list')
    else:
        form = ProposalRecommendationForm(instance=proposal)

    return render(request, 'proposals/proposal_recommendation.html', {
        'form': form,
        **proposal_detail_context(proposal),
    })


@login_required
def proposal_review(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk)

    if not request.user.is_admin:
        messages.error(request, 'Only administrators can review proposals.')
        return redirect('dashboard')

    if proposal.status != ProposalStatus.RECOMMENDED_APPROVAL:
        messages.error(request, 'This proposal must be recommended by Research & Extension Staff before admin review.')
        return redirect('proposal_detail', pk=proposal.pk)

    if request.method == 'POST':
        form = ProposalReviewForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.reviewed_by = request.user
            proposal.reviewed_at = timezone.now()
            proposal.save()
            if proposal.status == ProposalStatus.REJECTED:
                replace_proposal_requirements(
                    proposal,
                    form.cleaned_data.get('missing_requirements') or [],
                    form.cleaned_data.get('custom_requirements_list') or [],
                )
                log_proposal_event(
                    proposal,
                    ProposalTrackingEventType.ADMIN_REJECTED,
                    'Rejected by admin',
                    actor=request.user,
                    description=form.cleaned_data.get('review_notes') or 'Proposal was rejected and requires resubmission.',
                    status=proposal.status,
                )
            elif proposal.status == ProposalStatus.APPROVED:
                log_proposal_event(
                    proposal,
                    ProposalTrackingEventType.ADMIN_APPROVED,
                    'Approved by admin',
                    actor=request.user,
                    description=form.cleaned_data.get('review_notes') or 'Proposal was approved by the administrator.',
                    status=proposal.status,
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

    if proposal.status not in [ProposalStatus.REJECTED, ProposalStatus.RECOMMENDED_REVISION]:
        messages.error(request, 'Only rejected proposals can be resubmitted.')
        return redirect('proposal_detail', pk=proposal.pk)

    requirements = proposal.requirements.filter(is_resubmitted=False)

    if request.method == 'POST':
        form = ProposalResubmissionForm(request.POST, request.FILES, requirements=requirements)
        if form.is_valid():
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
                    if mapped_field == 'proposal_document':
                        document_version_file = requirement.uploaded_file

            proposal.status = ProposalStatus.PENDING_RECOMMENDATION
            proposal.recommended_by = None
            proposal.recommended_at = None
            proposal.reviewed_by = None
            proposal.reviewed_at = None
            proposal_update_fields = [
                'status',
                'recommended_by',
                'recommended_at',
                'reviewed_by',
                'reviewed_at',
                'date_updated',
                'proposal_document',
                'budget_pdf',
                'supporting_image',
            ]
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
            uploaded_labels = [
                requirement.label
                for requirement in requirements
                if requirement.is_resubmitted
            ]
            log_proposal_event(
                proposal,
                ProposalTrackingEventType.RESUBMITTED,
                'Requested documents resubmitted',
                actor=request.user,
                description=(
                    f"Uploaded: {', '.join(uploaded_labels)}"
                    if uploaded_labels
                    else 'Faculty resubmitted requested proposal documents.'
                ),
                status=proposal.status,
            )

            messages.success(request, 'Proposal resubmitted for review.')
            return redirect('proposal_detail', pk=proposal.pk)
    else:
        form = ProposalResubmissionForm(requirements=requirements)

    return render(request, 'proposals/proposal_detail.html', proposal_detail_context(
        proposal,
        resubmission_form=form,
    ))


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
        if 'abstract' in request.POST and len(abstract) < 50:
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
