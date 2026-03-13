from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

from .models import ExtensionRecord, ExtensionStatus, NarrativeReport, ReportQuarter
from .forms import ExtensionRecordForm, NarrativeReportForm
from proposals.models import Proposal, ProposalStatus, ProposalType
from users.models import UserRole


@login_required
def extension_list(request: HttpRequest) -> HttpResponse:
    user = request.user
    records = ExtensionRecord.objects.select_related('proposal', 'coordinator')

    if user.is_extension_staff:
        records = records.filter(
            Q(coordinator=user) | Q(team_members=user)
        )
    elif user.is_faculty:
        records = records.filter(proposal__faculty_author=user)

    status_filter = request.GET.get('status')
    if status_filter:
        records = records.filter(status=status_filter)

    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'extension/extension_list.html', {
        'page_obj': page_obj,
        'status_choices': ExtensionStatus.choices,
    })


@login_required
def extension_create(request: HttpRequest) -> HttpResponse:
    if not request.user.is_extension_staff and not request.user.is_admin:
        messages.error(request, 'Access denied. Extension staff only.')
        return redirect('dashboard')

    approved_proposals = Proposal.objects.filter(
        proposal_type=ProposalType.EXTENSION,
        status=ProposalStatus.APPROVED
    )

    if request.method == 'POST':
        form = ExtensionRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.coordinator = request.user
            record.save()
            form.save_m2m()
            messages.success(request, 'Extension record created successfully!')
            return redirect('extension_list')
    else:
        form = ExtensionRecordForm()
        form.fields['proposal'].queryset = approved_proposals

    return render(request, 'extension/extension_form.html', {'form': form})


@login_required
def extension_detail(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(ExtensionRecord, pk=pk)
    return render(request, 'extension/extension_detail.html', {'record': record})


@login_required
def extension_edit(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(ExtensionRecord, pk=pk)
    
    if record.coordinator != request.user and not request.user.is_admin:
        messages.error(request, 'You can only edit your own extension records.')
        return redirect('extension_list')

    if request.method == 'POST':
        form = ExtensionRecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Extension record updated successfully!')
            return redirect('extension_detail', pk=record.pk)
    else:
        form = ExtensionRecordForm(instance=record)

    return render(request, 'extension/extension_form.html', {'form': form, 'record': record})


@login_required
def add_narrative_report(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(ExtensionRecord, pk=pk)
    
    if not request.user.is_extension_staff and not request.user.is_admin:
        messages.error(request, 'Access denied. Extension staff only.')
        return redirect('extension_detail', pk=pk)
        
    if request.method == 'POST':
        form = NarrativeReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.extension_record = record
            report.submitted_by = request.user
            report.save()
            messages.success(request, 'Narrative report added successfully!')
            return redirect('extension_detail', pk=record.pk)
    else:
        form = NarrativeReportForm()
        
    return render(request, 'extension/narrative_report_form.html', {'form': form, 'record': record})


@login_required
def quarterly_reports_list(request: HttpRequest) -> HttpResponse:
    reports = NarrativeReport.objects.select_related('extension_record', 'submitted_by')
    
    year_filter = request.GET.get('year')
    quarter_filter = request.GET.get('quarter')
    
    if year_filter:
        reports = reports.filter(report_year=year_filter)
    if quarter_filter:
        reports = reports.filter(quarter=quarter_filter)
        
    available_years = NarrativeReport.objects.values_list('report_year', flat=True).distinct().order_by('-report_year')
    quarters = ReportQuarter.choices
    
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'available_years': available_years,
        'quarters': quarters,
        'current_year_filter': year_filter,
        'current_quarter_filter': quarter_filter,
    }
    
    return render(request, 'extension/quarterly_reports_list.html', context)
