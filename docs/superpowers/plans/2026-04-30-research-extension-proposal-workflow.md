# Research Extension Proposal Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the two-stage proposal workflow where Research and Extension Staff recommends first, then Admin makes the final decision.

**Architecture:** Merge the old research and extension staff roles into one user role, then extend `Proposal` with ownership, recommendation, and project progress fields. Keep workflow checks in proposal forms/views, and update dashboards, reports, and templates to use the merged staff role and new statuses.

**Tech Stack:** Django 4.2, Django `TestCase`, SQLite local database, Tailwind/Alpine templates.

---

## File Structure

- Modify `users/models.py`: replace separate staff role choices with `RESEARCH_EXTENSION_STAFF`, add merged helper property, and keep compatibility helpers during the transition.
- Create `users/migrations/0003_merge_research_extension_staff_roles.py`: convert old `RESEARCH_STAFF` and `EXTENSION_STAFF` rows to the new role value.
- Modify `users/tests.py`: cover role merge helpers and migration-facing role values.
- Modify `proposals/models.py`: add proposal ownership fields, recommendation fields, project progress choices, and new proposal statuses.
- Create `proposals/migrations/0005_two_stage_proposal_workflow.py`: add new fields and migrate old `PENDING` proposals to `PENDING_RECOMMENDATION`.
- Modify `proposals/forms.py`: add faculty selector for staff submissions, add staff recommendation form, update admin review choices.
- Modify `proposals/views.py`: allow staff proposal submission on behalf of faculty, add staff recommendation view, gate admin review, and return resubmissions to staff review.
- Modify `proposals/urls.py`: add the staff recommendation route.
- Modify `templates/proposals/proposal_form.html`: render the staff-only faculty author selector.
- Modify `templates/proposals/proposal_list.html`: show recommendation/admin actions according to role and status.
- Modify `templates/proposals/proposal_detail.html` and `templates/proposals/proposal_research_detail.html`: show submitter, staff recommendation, and project progress fields.
- Create `templates/proposals/proposal_recommendation.html`: staff recommendation page.
- Modify `portal/views.py`: route merged staff to one dashboard and compute recommendation/project metrics.
- Create or repurpose `templates/portal/research_extension_dashboard.html`: merged staff dashboard.
- Modify `templates/base.html`: update staff navigation labels if old research/extension staff labels are visible.
- Modify `core/context_processors.py`: update notification counts for merged staff and new statuses.
- Modify `core/reports.py` and `templates/core/comprehensive_reports.html`: add independent approval status, project progress, department, and submitter filters.
- Modify `proposals/tests.py`, `portal/tests.py`, and `core/tests_reports.py`: cover the new workflow and update stale role assumptions.

---

### Task 1: Merge Research and Extension Staff User Role

**Files:**
- Modify: `users/models.py`
- Create: `users/migrations/0003_merge_research_extension_staff_roles.py`
- Modify: `users/tests.py`
- Modify: `portal/tests.py`

- [ ] **Step 1: Write failing role tests**

Add this to `users/tests.py`:

```python
from django.test import TestCase

from users.models import CustomUser, UserRole


class UserRoleMergeTests(TestCase):
    def test_merged_research_extension_staff_role_exists(self):
        self.assertEqual(UserRole.RESEARCH_EXTENSION_STAFF, 'RESEARCH_EXTENSION_STAFF')
        labels = dict(UserRole.choices)
        self.assertEqual(labels[UserRole.RESEARCH_EXTENSION_STAFF], 'Research & Extension Staff')

    def test_merged_staff_helper_identifies_staff_user(self):
        user = CustomUser.objects.create_user(
            username='staff',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
        )

        self.assertTrue(user.is_research_extension_staff)
        self.assertTrue(user.is_research_staff)
        self.assertTrue(user.is_extension_staff)
        self.assertFalse(user.is_faculty)
```

Update `portal/tests.py` by replacing the two separate dashboard tests with:

```python
    def test_research_extension_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('research-extension-user', UserRole.RESEARCH_EXTENSION_STAFF)

        self.assert_dashboard_shell(user, 'Research & Extension Workspace')
```

- [ ] **Step 2: Run role tests to verify they fail**

Run: `python manage.py test users portal.tests.DashboardVisualRefreshTests.test_research_extension_dashboard_uses_formal_operations_layout`

Expected: FAIL because `UserRole.RESEARCH_EXTENSION_STAFF` and `is_research_extension_staff` do not exist.

- [ ] **Step 3: Update `users/models.py` role choices and helpers**

Replace `UserRole` and the staff helper properties with:

```python
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    FACULTY = 'FACULTY', 'Faculty'
    RESEARCH_EXTENSION_STAFF = 'RESEARCH_EXTENSION_STAFF', 'Research & Extension Staff'


class Department(models.TextChoices):
    SOCJE = 'SOCJE', 'SOCJE'
    SAFES = 'SAFES', 'SAFES'
    STE = 'STE', 'STE'
    SCS = 'SCS', 'SCS'
```

Keep the existing `CustomUser` class and replace the staff properties with:

```python
    @property
    def is_research_extension_staff(self):
        return self.role == UserRole.RESEARCH_EXTENSION_STAFF

    @property
    def is_research_staff(self):
        return self.is_research_extension_staff

    @property
    def is_extension_staff(self):
        return self.is_research_extension_staff
```

- [ ] **Step 4: Add the role migration**

Create `users/migrations/0003_merge_research_extension_staff_roles.py`:

```python
from django.db import migrations, models


def merge_staff_roles(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    CustomUser.objects.filter(role__in=['RESEARCH_STAFF', 'EXTENSION_STAFF']).update(
        role='RESEARCH_EXTENSION_STAFF'
    )


def split_staff_roles(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    CustomUser.objects.filter(role='RESEARCH_EXTENSION_STAFF').update(role='RESEARCH_STAFF')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_customuser_department'),
    ]

    operations = [
        migrations.RunPython(merge_staff_roles, split_staff_roles),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Administrator'),
                    ('FACULTY', 'Faculty'),
                    ('RESEARCH_EXTENSION_STAFF', 'Research & Extension Staff'),
                ],
                default='FACULTY',
                max_length=30,
            ),
        ),
    ]
```

- [ ] **Step 5: Run role tests to verify they pass**

Run: `python manage.py test users portal.tests.DashboardVisualRefreshTests.test_research_extension_dashboard_uses_formal_operations_layout`

Expected: PASS after the dashboard routing/template work in Task 5. During Task 1 only the `users` tests should pass; the portal test can remain failing until Task 5.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add users/models.py users/migrations/0003_merge_research_extension_staff_roles.py users/tests.py portal/tests.py
git commit -m "feat: merge research and extension staff role"
```

---

### Task 2: Add Proposal Workflow Fields and Statuses

**Files:**
- Modify: `proposals/models.py`
- Create: `proposals/migrations/0005_two_stage_proposal_workflow.py`
- Modify: `proposals/tests.py`

- [ ] **Step 1: Write failing model workflow tests**

Add this class to `proposals/tests.py`:

```python
class ProposalWorkflowModelTests(TestCase):
    def setUp(self):
        self.faculty = CustomUser.objects.create_user(
            username='workflow-faculty',
            password='password',
            role=UserRole.FACULTY,
        )
        self.staff = CustomUser.objects.create_user(
            username='workflow-staff',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
        )

    def test_new_proposal_defaults_to_pending_recommendation(self):
        proposal = Proposal.objects.create(
            title='Workflow Proposal Title',
            abstract='This abstract is long enough for the workflow model test.',
            full_description='Detailed proposal description for workflow model test.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            submitted_by=self.faculty,
        )

        self.assertEqual(proposal.status, ProposalStatus.PENDING_RECOMMENDATION)
        self.assertEqual(proposal.submitted_by, self.faculty)
        self.assertFalse(proposal.submitted_on_behalf)
        self.assertEqual(proposal.project_progress_status, '')

    def test_staff_submission_can_record_on_behalf_owner_and_submitter(self):
        proposal = Proposal.objects.create(
            title='Staff Submitted Proposal',
            abstract='This abstract is long enough for staff submission workflow.',
            full_description='Detailed proposal description for staff submission.',
            proposal_type=ProposalType.EXTENSION,
            faculty_author=self.faculty,
            submitted_by=self.staff,
            submitted_on_behalf=True,
        )

        self.assertEqual(proposal.faculty_author, self.faculty)
        self.assertEqual(proposal.submitted_by, self.staff)
        self.assertTrue(proposal.submitted_on_behalf)
```

- [ ] **Step 2: Run model tests to verify they fail**

Run: `python manage.py test proposals.tests.ProposalWorkflowModelTests`

Expected: FAIL because the new statuses and proposal fields do not exist.

- [ ] **Step 3: Update `proposals/models.py` statuses and fields**

Replace `ProposalStatus` with:

```python
class ProposalStatus(models.TextChoices):
    PENDING_RECOMMENDATION = 'PENDING_RECOMMENDATION', 'Pending Staff Recommendation'
    RECOMMENDED_APPROVAL = 'RECOMMENDED_APPROVAL', 'Recommended for Admin Approval'
    RECOMMENDED_REVISION = 'RECOMMENDED_REVISION', 'Recommended for Revision'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
```

Add this class below `ProposalType`:

```python
class ProjectProgressStatus(models.TextChoices):
    ONGOING = 'ONGOING', 'Ongoing'
    PRESENTED = 'PRESENTED', 'Presented'
    COMPLETED = 'COMPLETED', 'Completed'
```

In `Proposal`, add these fields after `faculty_author`:

```python
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_submitted'
    )
    submitted_on_behalf = models.BooleanField(default=False)
```

Replace the `status` default with:

```python
        default=ProposalStatus.PENDING_RECOMMENDATION
```

Add staff recommendation fields before `reviewed_by`:

```python
    recommended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_recommended'
    )
    recommendation_notes = models.TextField(blank=True)
    recommended_at = models.DateTimeField(blank=True, null=True)
```

Add project progress after `reviewed_at`:

```python
    project_progress_status = models.CharField(
        max_length=20,
        choices=ProjectProgressStatus.choices,
        blank=True
    )
```

- [ ] **Step 4: Add the proposal workflow migration**

Create `proposals/migrations/0005_two_stage_proposal_workflow.py`:

```python
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_statuses_forward(apps, schema_editor):
    Proposal = apps.get_model('proposals', 'Proposal')
    Proposal.objects.filter(status='PENDING').update(status='PENDING_RECOMMENDATION')


def migrate_statuses_backward(apps, schema_editor):
    Proposal = apps.get_model('proposals', 'Proposal')
    Proposal.objects.filter(status='PENDING_RECOMMENDATION').update(status='PENDING')
    Proposal.objects.filter(status='RECOMMENDED_APPROVAL').update(status='PENDING')
    Proposal.objects.filter(status='RECOMMENDED_REVISION').update(status='REJECTED')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proposals', '0004_proposalrequirement'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='submitted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proposals_submitted',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='proposal',
            name='submitted_on_behalf',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='proposal',
            name='recommended_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proposals_recommended',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='proposal',
            name='recommendation_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='recommended_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='project_progress_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ONGOING', 'Ongoing'),
                    ('PRESENTED', 'Presented'),
                    ('COMPLETED', 'Completed'),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_statuses_forward, migrate_statuses_backward),
        migrations.AlterField(
            model_name='proposal',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_RECOMMENDATION', 'Pending Staff Recommendation'),
                    ('RECOMMENDED_APPROVAL', 'Recommended for Admin Approval'),
                    ('RECOMMENDED_REVISION', 'Recommended for Revision'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected'),
                ],
                default='PENDING_RECOMMENDATION',
                max_length=30,
            ),
        ),
    ]
```

- [ ] **Step 5: Run model tests to verify they pass**

Run: `python manage.py test proposals.tests.ProposalWorkflowModelTests`

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add proposals/models.py proposals/migrations/0005_two_stage_proposal_workflow.py proposals/tests.py
git commit -m "feat: add proposal workflow tracking fields"
```

---

### Task 3: Implement Submission, Recommendation, Admin Gate, and Resubmission Logic

**Files:**
- Modify: `proposals/forms.py`
- Modify: `proposals/views.py`
- Modify: `proposals/urls.py`
- Modify: `proposals/tests.py`

- [ ] **Step 1: Write failing workflow view tests**

Add this class to `proposals/tests.py`:

```python
class ProposalTwoStageWorkflowViewTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='workflow-admin',
            password='password',
            role=UserRole.ADMIN,
        )
        self.faculty = CustomUser.objects.create_user(
            username='workflow-faculty-view',
            password='password',
            role=UserRole.FACULTY,
        )
        self.staff = CustomUser.objects.create_user(
            username='workflow-staff-view',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
        )
        self.proposal = Proposal.objects.create(
            title='Two Stage Review Proposal',
            abstract='This proposal abstract has enough content for two stage review.',
            full_description='Full description for a proposal that uses two stage review.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            submitted_by=self.faculty,
        )

    def proposal_payload(self, **overrides):
        payload = {
            'title': 'Submitted Workflow Proposal',
            'abstract': 'This abstract is long enough to satisfy proposal validation for workflow.',
            'full_description': 'This full description is enough for a submitted workflow proposal.',
            'proposal_type': ProposalType.RESEARCH,
            'research_staff': '',
        }
        payload.update(overrides)
        return payload

    def test_faculty_submission_starts_at_staff_recommendation(self):
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.post(reverse('proposal_create'), self.proposal_payload())

        created = Proposal.objects.get(title='Submitted Workflow Proposal')
        self.assertRedirects(response, reverse('proposal_list'))
        self.assertEqual(created.status, ProposalStatus.PENDING_RECOMMENDATION)
        self.assertEqual(created.faculty_author, self.faculty)
        self.assertEqual(created.submitted_by, self.faculty)
        self.assertFalse(created.submitted_on_behalf)

    def test_staff_can_submit_on_behalf_of_faculty(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.post(
            reverse('proposal_create'),
            self.proposal_payload(faculty_author=self.faculty.pk),
        )

        created = Proposal.objects.get(title='Submitted Workflow Proposal')
        self.assertRedirects(response, reverse('proposal_list'))
        self.assertEqual(created.status, ProposalStatus.PENDING_RECOMMENDATION)
        self.assertEqual(created.faculty_author, self.faculty)
        self.assertEqual(created.submitted_by, self.staff)
        self.assertTrue(created.submitted_on_behalf)

    def test_admin_cannot_review_before_staff_recommendation(self):
        self.client.login(username='workflow-admin', password='password')

        response = self.client.get(reverse('proposal_review', args=[self.proposal.pk]))

        self.assertRedirects(response, reverse('proposal_detail', args=[self.proposal.pk]))

    def test_staff_can_recommend_proposal_for_admin_approval(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.RECOMMENDED_APPROVAL,
                'recommendation_notes': 'Documents are complete and ready for admin.',
            },
        )

        self.assertRedirects(response, reverse('proposal_list'))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.RECOMMENDED_APPROVAL)
        self.assertEqual(self.proposal.recommended_by, self.staff)
        self.assertIsNotNone(self.proposal.recommended_at)

    def test_staff_revision_requires_notes(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.RECOMMENDED_REVISION,
                'recommendation_notes': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recommendation notes are required when requesting revision.')
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.PENDING_RECOMMENDATION)

    def test_admin_can_approve_after_staff_recommendation(self):
        self.proposal.status = ProposalStatus.RECOMMENDED_APPROVAL
        self.proposal.recommended_by = self.staff
        self.proposal.recommended_at = timezone.now()
        self.proposal.save()
        self.client.login(username='workflow-admin', password='password')

        response = self.client.post(
            reverse('proposal_review', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.APPROVED,
                'review_notes': 'Final approval granted.',
            },
        )

        self.assertRedirects(response, reverse('proposal_list'))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.APPROVED)
        self.assertEqual(self.proposal.reviewed_by, self.admin)

    def test_revision_resubmission_returns_to_staff_recommendation(self):
        self.proposal.status = ProposalStatus.RECOMMENDED_REVISION
        self.proposal.recommendation_notes = 'Upload revised budget.'
        self.proposal.save()
        requirement = ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='budget_pdf',
            label='Budget Letter or Budget PDF',
        )
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.post(
            reverse('proposal_resubmit', args=[self.proposal.pk]),
            {
                f'requirement_{requirement.pk}': SimpleUploadedFile(
                    'budget.pdf',
                    b'%PDF-1.4 budget',
                    content_type='application/pdf',
                ),
            },
        )

        self.assertRedirects(response, reverse('proposal_detail', args=[self.proposal.pk]))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.PENDING_RECOMMENDATION)
        self.assertIsNone(self.proposal.recommended_by)
        self.assertIsNone(self.proposal.recommended_at)
```

Add `from django.utils import timezone` near the top of `proposals/tests.py` if it is not already imported.

- [ ] **Step 2: Run workflow view tests to verify they fail**

Run: `python manage.py test proposals.tests.ProposalTwoStageWorkflowViewTests`

Expected: FAIL because `proposal_recommend`, staff submission, and admin gating do not exist.

- [ ] **Step 3: Update `proposals/forms.py`**

Add imports:

```python
from users.models import CustomUser, UserRole
```

Update `ProposalForm.__init__`:

```python
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['research_staff'].required = False
        if user and user.is_research_extension_staff:
            self.fields['faculty_author'] = forms.ModelChoiceField(
                queryset=CustomUser.objects.filter(role=UserRole.FACULTY, is_active=True).order_by('last_name', 'first_name', 'username'),
                required=True,
                label='Faculty Author',
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white'
                }),
            )
        elif 'faculty_author' in self.fields:
            self.fields.pop('faculty_author')
```

Add this form below `ProposalReviewForm`:

```python
class ProposalRecommendationForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            (ProposalStatus.RECOMMENDED_APPROVAL, 'Recommend for admin approval'),
            (ProposalStatus.RECOMMENDED_REVISION, 'Request revision or resubmission'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )

    class Meta:
        model = Proposal
        fields = ['status', 'recommendation_notes']
        widgets = {
            'recommendation_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 4,
                'placeholder': 'Explain your recommendation for the admin or the revisions needed from faculty'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        notes = (cleaned_data.get('recommendation_notes') or '').strip()
        if status == ProposalStatus.RECOMMENDED_REVISION and not notes:
            self.add_error('recommendation_notes', 'Recommendation notes are required when requesting revision.')
        return cleaned_data
```

Update `ProposalReviewForm.status` choices to keep only final admin decisions:

```python
    status = forms.ChoiceField(
        choices=[
            (ProposalStatus.APPROVED, 'Approve'),
            (ProposalStatus.REJECTED, 'Reject and request resubmission'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
```

- [ ] **Step 4: Update `proposals/views.py` imports**

Change the forms import to:

```python
from .forms import ProposalForm, ProposalRecommendationForm, ProposalReviewForm, ProposalResubmissionForm
```

Add `CustomUser` to the users import:

```python
from users.models import CustomUser, UserRole
```

- [ ] **Step 5: Update proposal list role scoping**

In `proposal_list`, replace the staff branches with:

```python
    elif user.is_research_extension_staff:
        proposals = proposals.filter(
            Q(status=ProposalStatus.PENDING_RECOMMENDATION) |
            Q(status=ProposalStatus.RECOMMENDED_APPROVAL) |
            Q(status=ProposalStatus.RECOMMENDED_REVISION) |
            Q(submitted_by=user)
        )
```

- [ ] **Step 6: Update proposal creation**

Replace the permission check and form handling in `proposal_create` with:

```python
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
```

Keep the existing document version block and success redirect after `proposal.save()`.

Change the GET branch to:

```python
    else:
        form = ProposalForm(user=request.user)
```

- [ ] **Step 7: Add staff recommendation view**

Add this view to `proposals/views.py` before `proposal_review`:

```python
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
            messages.success(request, 'Proposal recommendation submitted.')
            return redirect('proposal_list')
    else:
        form = ProposalRecommendationForm(instance=proposal)

    return render(request, 'proposals/proposal_recommendation.html', {
        'form': form,
        'proposal': proposal,
        'requirements': proposal.requirements.all(),
    })
```

- [ ] **Step 8: Gate admin review**

At the top of `proposal_review`, after the admin permission check, add:

```python
    if proposal.status != ProposalStatus.RECOMMENDED_APPROVAL:
        messages.error(request, 'This proposal must be recommended by Research & Extension Staff before admin review.')
        return redirect('proposal_detail', pk=proposal.pk)
```

- [ ] **Step 9: Update resubmission statuses**

In `proposal_resubmit`, replace:

```python
    if proposal.status != ProposalStatus.REJECTED:
```

with:

```python
    if proposal.status not in [ProposalStatus.REJECTED, ProposalStatus.RECOMMENDED_REVISION]:
```

Replace:

```python
            proposal.status = ProposalStatus.PENDING
            proposal.reviewed_by = None
            proposal.reviewed_at = None
```

with:

```python
            proposal.status = ProposalStatus.PENDING_RECOMMENDATION
            proposal.recommended_by = None
            proposal.recommended_at = None
            proposal.reviewed_by = None
            proposal.reviewed_at = None
```

Include `recommended_by`, `recommended_at`, and `recommendation_notes` in `proposal_update_fields`:

```python
            proposal_update_fields = [
                'status',
                'recommended_by',
                'recommended_at',
                'reviewed_by',
                'reviewed_at',
                'date_updated',
            ]
```

- [ ] **Step 10: Add recommendation URL**

In `proposals/urls.py`, add:

```python
    path('<int:pk>/recommend/', views.proposal_recommend, name='proposal_recommend'),
```

Place it before the `review/` route.

- [ ] **Step 11: Run workflow view tests to verify they pass**

Run: `python manage.py test proposals.tests.ProposalTwoStageWorkflowViewTests`

Expected: PASS.

- [ ] **Step 12: Commit Task 3**

Run:

```bash
git add proposals/forms.py proposals/views.py proposals/urls.py proposals/tests.py
git commit -m "feat: add staff proposal recommendation workflow"
```

---

### Task 4: Update Proposal Templates for the New Workflow

**Files:**
- Modify: `templates/proposals/proposal_form.html`
- Modify: `templates/proposals/proposal_list.html`
- Modify: `templates/proposals/proposal_detail.html`
- Modify: `templates/proposals/proposal_research_detail.html`
- Create: `templates/proposals/proposal_recommendation.html`
- Modify: `proposals/tests.py`

- [ ] **Step 1: Write failing template tests**

Add these tests to `ProposalTwoStageWorkflowViewTests`:

```python
    def test_staff_create_page_shows_faculty_author_selector(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_create'))

        self.assertContains(response, 'Faculty Author')
        self.assertContains(response, self.faculty.username)

    def test_staff_list_shows_recommend_action_for_pending_recommendation(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_list'))

        self.assertContains(response, reverse('proposal_recommend', args=[self.proposal.pk]))

    def test_proposal_detail_shows_submitter_and_recommendation_metadata(self):
        self.proposal.status = ProposalStatus.RECOMMENDED_APPROVAL
        self.proposal.recommended_by = self.staff
        self.proposal.recommended_at = timezone.now()
        self.proposal.recommendation_notes = 'Ready for admin review.'
        self.proposal.save()
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.get(reverse('proposal_detail', args=[self.proposal.pk]))

        self.assertContains(response, 'Submitted By')
        self.assertContains(response, 'Staff Recommendation')
        self.assertContains(response, 'Ready for admin review.')
```

- [ ] **Step 2: Run template tests to verify they fail**

Run: `python manage.py test proposals.tests.ProposalTwoStageWorkflowViewTests`

Expected: FAIL because the templates do not render the new fields and actions.

- [ ] **Step 3: Render staff faculty selector in `proposal_form.html`**

After the proposal type card in Step 1, add:

```django
                {% if form.faculty_author %}
                <div class="form-section bg-gradient-to-br from-slate-50 to-blue-50 rounded-xl p-5 border border-slate-100 md:col-span-2">
                    <div class="flex items-center mb-3">
                        <div class="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center mr-3">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                        </div>
                        <h3 class="font-semibold text-gray-800">Submit on Behalf of Faculty</h3>
                    </div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Faculty Author *</label>
                    {{ form.faculty_author }}
                    {% if form.faculty_author.errors %}
                    <p class="text-red-500 text-sm mt-1">{{ form.faculty_author.errors.0 }}</p>
                    {% endif %}
                </div>
                {% endif %}
```

- [ ] **Step 4: Update proposal list actions**

In `proposal_list.html`, replace the admin review action condition:

```django
                                {% if user.is_admin and proposal.status == 'PENDING' %}
```

with:

```django
                                {% if user.is_research_extension_staff and proposal.status == 'PENDING_RECOMMENDATION' %}
                                <a href="{% url 'proposal_recommend' proposal.pk %}" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-1" title="Recommend Proposal">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                </a>
                                {% endif %}

                                {% if user.is_admin and proposal.status == 'RECOMMENDED_APPROVAL' %}
```

- [ ] **Step 5: Add detail metadata**

In both detail templates, add these blocks in the metadata grid:

```django
                <p><span class="font-medium">Submitted By:</span> {{ proposal.submitted_by.get_full_name|default:proposal.submitted_by.username|default:"Unknown" }}</p>
                {% if proposal.submitted_on_behalf %}
                <p><span class="font-medium">Submission Type:</span> Submitted on behalf of faculty</p>
                {% endif %}
                {% if proposal.project_progress_status %}
                <p><span class="font-medium">Project Progress:</span> {{ proposal.get_project_progress_status_display }}</p>
                {% endif %}
```

Add this recommendation summary before admin review notes:

```django
        {% if proposal.recommended_by or proposal.status == 'RECOMMENDED_REVISION' or proposal.status == 'RECOMMENDED_APPROVAL' %}
        <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6">
            <h2 class="text-lg font-semibold mb-2 text-blue-900">Staff Recommendation</h2>
            <p class="text-gray-700 whitespace-pre-line">{{ proposal.recommendation_notes|default:"No recommendation notes provided." }}</p>
            {% if proposal.recommended_by %}
            <p class="text-sm text-gray-500 mt-2">Recommended by {{ proposal.recommended_by.get_full_name|default:proposal.recommended_by.username }} on {{ proposal.recommended_at|date:"M d, Y" }}</p>
            {% endif %}
        </div>
        {% endif %}
```

- [ ] **Step 6: Create recommendation template**

Create `templates/proposals/proposal_recommendation.html`:

```django
{% extends 'base.html' %}

{% block page_title %}Recommend Proposal{% endblock %}

{% block content %}
<div class="max-w-5xl mx-auto">
    <div class="grid lg:grid-cols-[1fr_380px] gap-6">
        <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
            <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Staff Recommendation</p>
            <h1 class="text-2xl font-bold text-slate-900 mt-1">{{ proposal.title }}</h1>
            <div class="grid sm:grid-cols-2 gap-4 text-sm text-slate-600 my-6">
                <div class="rounded-lg bg-slate-50 border border-slate-100 p-4">
                    <p class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Faculty Author</p>
                    <p class="font-semibold text-slate-800">{{ proposal.faculty_author.get_full_name|default:proposal.faculty_author.username }}</p>
                </div>
                <div class="rounded-lg bg-slate-50 border border-slate-100 p-4">
                    <p class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Submitted By</p>
                    <p class="font-semibold text-slate-800">{{ proposal.submitted_by.get_full_name|default:proposal.submitted_by.username|default:"Unknown" }}</p>
                </div>
            </div>
            <h2 class="text-sm font-bold text-slate-900 mb-2">Abstract</h2>
            <p class="text-sm leading-6 text-slate-700 whitespace-pre-line mb-6">{{ proposal.abstract }}</p>
            <h2 class="text-sm font-bold text-slate-900 mb-2">Full Description</h2>
            <p class="text-sm leading-6 text-slate-700 whitespace-pre-line">{{ proposal.full_description }}</p>
        </section>

        <aside class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
            <h2 class="text-lg font-bold text-slate-900 mb-1">Recommendation</h2>
            <p class="text-sm text-slate-500 mb-5">Send this proposal to admin or return it to faculty for revision.</p>
            <form method="post" class="space-y-6">
                {% csrf_token %}
                <div class="space-y-2">
                    {% for radio in form.status %}
                    <label class="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                        {{ radio.tag }}
                        <span>{{ radio.choice_label }}</span>
                    </label>
                    {% endfor %}
                </div>
                {% if form.status.errors %}
                <p class="text-red-600 text-sm">{{ form.status.errors.0 }}</p>
                {% endif %}

                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Recommendation Notes</label>
                    {{ form.recommendation_notes }}
                    {% if form.recommendation_notes.errors %}
                    <p class="text-red-600 text-sm mt-2">{{ form.recommendation_notes.errors.0 }}</p>
                    {% endif %}
                </div>

                <div class="flex flex-col sm:flex-row gap-3">
                    <button type="submit" class="inline-flex justify-center px-5 py-2.5 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800">Submit Recommendation</button>
                    <a href="{% url 'proposal_list' %}" class="inline-flex justify-center px-5 py-2.5 border border-slate-300 rounded-lg font-semibold text-slate-700 hover:bg-slate-50">Cancel</a>
                </div>
            </form>
        </aside>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 7: Run template tests to verify they pass**

Run: `python manage.py test proposals.tests.ProposalTwoStageWorkflowViewTests`

Expected: PASS.

- [ ] **Step 8: Commit Task 4**

Run:

```bash
git add templates/proposals/proposal_form.html templates/proposals/proposal_list.html templates/proposals/proposal_detail.html templates/proposals/proposal_research_detail.html templates/proposals/proposal_recommendation.html proposals/tests.py
git commit -m "feat: update proposal workflow screens"
```

---

### Task 5: Merge Staff Dashboard, Notifications, and Navigation

**Files:**
- Modify: `portal/views.py`
- Create: `templates/portal/research_extension_dashboard.html`
- Modify: `core/context_processors.py`
- Modify: `templates/base.html`
- Modify: `portal/tests.py`

- [ ] **Step 1: Write failing dashboard and notification tests**

Update `portal/tests.py` with:

```python
    def test_research_extension_dashboard_shows_recommendation_queue(self):
        staff = self.make_user('queue-staff', UserRole.RESEARCH_EXTENSION_STAFF)
        faculty = self.make_user('queue-faculty', UserRole.FACULTY)
        from proposals.models import Proposal, ProposalStatus, ProposalType

        Proposal.objects.create(
            title='Pending Queue Proposal',
            abstract='Abstract for pending queue proposal.',
            full_description='Full description for pending queue proposal.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=faculty,
            submitted_by=faculty,
            status=ProposalStatus.PENDING_RECOMMENDATION,
        )

        self.client.force_login(staff)
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Research & Extension Workspace')
        self.assertContains(response, 'Pending Recommendations')
        self.assertContains(response, 'Pending Queue Proposal')
```

- [ ] **Step 2: Run dashboard tests to verify they fail**

Run: `python manage.py test portal`

Expected: FAIL because the dashboard route still branches to separate research or extension dashboards.

- [ ] **Step 3: Update `portal/views.py` routing**

In `dashboard`, replace the staff branches with:

```python
    elif user.is_research_extension_staff:
        return research_extension_dashboard(request)
```

Add this view:

```python
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
```

- [ ] **Step 4: Create merged staff dashboard template**

Create `templates/portal/research_extension_dashboard.html` using the existing dashboard shell attributes:

```django
{% extends 'base.html' %}

{% block page_title %}Research & Extension Dashboard{% endblock %}

{% block content %}
<div data-dashboard-shell data-dashboard-variant="executive-clean" class="max-w-7xl mx-auto space-y-6">
    <section class="rounded-lg bg-slate-900 text-white p-6">
        <p class="text-sm uppercase tracking-wider text-slate-300">Operational summary</p>
        <h1 class="text-2xl font-bold mt-1">Research & Extension Workspace</h1>
        <p class="text-slate-300 mt-2">Review faculty proposals before admin approval and monitor approved project progress.</p>
    </section>

    <section class="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="metric-card bg-white border border-slate-200 rounded-lg p-4">
            <p class="text-xs font-bold uppercase text-slate-500">Pending Recommendations</p>
            <p class="text-2xl font-bold text-slate-900">{{ total_pending_recommendations }}</p>
        </div>
        <div class="metric-card bg-white border border-slate-200 rounded-lg p-4">
            <p class="text-xs font-bold uppercase text-slate-500">Recommended For Admin</p>
            <p class="text-2xl font-bold text-slate-900">{{ total_recommended_for_admin }}</p>
        </div>
        <div class="metric-card bg-white border border-slate-200 rounded-lg p-4">
            <p class="text-xs font-bold uppercase text-slate-500">Ongoing</p>
            <p class="text-2xl font-bold text-slate-900">{{ ongoing_projects }}</p>
        </div>
        <div class="metric-card bg-white border border-slate-200 rounded-lg p-4">
            <p class="text-xs font-bold uppercase text-slate-500">Presented</p>
            <p class="text-2xl font-bold text-slate-900">{{ presented_projects }}</p>
        </div>
        <div class="metric-card bg-white border border-slate-200 rounded-lg p-4">
            <p class="text-xs font-bold uppercase text-slate-500">Completed</p>
            <p class="text-2xl font-bold text-slate-900">{{ completed_projects }}</p>
        </div>
    </section>

    <section class="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
            <h2 class="font-bold text-slate-900">Pending Recommendations</h2>
            <a href="{% url 'proposal_create' %}" class="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold">Submit on Behalf</a>
        </div>
        <div class="divide-y divide-slate-100">
            {% for proposal in pending_recommendations %}
            <div class="px-5 py-4 flex items-center justify-between gap-4">
                <div>
                    <p class="font-semibold text-slate-800">{{ proposal.title }}</p>
                    <p class="text-xs text-slate-500">{{ proposal.faculty_author.get_full_name|default:proposal.faculty_author.username }}</p>
                </div>
                <a href="{% url 'proposal_recommend' proposal.pk %}" class="px-3 py-2 rounded-lg bg-blue-50 text-blue-700 text-sm font-semibold">Recommend</a>
            </div>
            {% empty %}
            <p class="px-5 py-8 text-sm text-slate-500">No proposals are waiting for recommendation.</p>
            {% endfor %}
        </div>
    </section>
</div>
{% endblock %}
```

- [ ] **Step 5: Update notifications**

In `core/context_processors.py`, replace old staff notification branches with:

```python
        elif user.is_research_extension_staff:
            pending_recommendations = Proposal.objects.filter(status=ProposalStatus.PENDING_RECOMMENDATION).count()
            if pending_recommendations > 0:
                notifications.append({
                    'title': 'Pending Recommendations',
                    'message': f'There are {pending_recommendations} proposals waiting for staff recommendation.',
                    'url': '/proposals/?status=PENDING_RECOMMENDATION',
                    'type': 'info',
                })
                unread_count += pending_recommendations
```

- [ ] **Step 6: Update navigation labels**

In `templates/base.html`, replace visible `Research Staff` or `Extension Staff` staff-dashboard labels with `Research & Extension Staff`. Keep faculty-facing `Research` and `Extension` content labels where they describe project type rather than user role.

- [ ] **Step 7: Run dashboard tests to verify they pass**

Run: `python manage.py test portal`

Expected: PASS.

- [ ] **Step 8: Commit Task 5**

Run:

```bash
git add portal/views.py templates/portal/research_extension_dashboard.html core/context_processors.py templates/base.html portal/tests.py
git commit -m "feat: add merged research extension dashboard"
```

---

### Task 6: Update Reports for Approval, Progress, Department, and Submitter Filters

**Files:**
- Modify: `core/reports.py`
- Modify: `templates/core/comprehensive_reports.html`
- Modify: `core/tests_reports.py`

- [ ] **Step 1: Write failing report filter tests**

Add this test to `core/tests_reports.py`:

```python
    def test_reports_filter_by_approval_progress_department_and_submitter(self):
        self.faculty.department = 'SCS'
        self.faculty.save()
        staff_submitted = Proposal.objects.create(
            title='Staff Submitted SCS Proposal',
            abstract='Staff submitted report filter abstract.',
            full_description='Staff submitted report filter description.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            submitted_by=self.research_staff,
            submitted_on_behalf=True,
            status=ProposalStatus.APPROVED,
            project_progress_status='PRESENTED',
        )
        self.client.login(username='admin', password='password')

        response = self.client.get(
            reverse('comprehensive_reports'),
            {
                'approval_status': ProposalStatus.APPROVED,
                'project_progress': 'PRESENTED',
                'department': 'SCS',
                'submitter_type': 'staff_on_behalf',
            },
        )

        self.assertContains(response, 'Staff Submitted SCS Proposal')
        self.assertContains(response, 'approval_status=APPROVED')
        self.assertContains(response, 'project_progress=PRESENTED')
        self.assertContains(response, 'department=SCS')
        self.assertContains(response, 'submitter_type=staff_on_behalf')
        self.assertNotContains(response, 'Other Faculty Proposal')
```

Also update `setUp` staff users:

```python
        self.research_staff = CustomUser.objects.create_user(
            username='researcher',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
        )
        self.extension_staff = CustomUser.objects.create_user(
            username='extension',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
        )
```

- [ ] **Step 2: Run report tests to verify they fail**

Run: `python manage.py test core.tests_reports`

Expected: FAIL because the new report filters are not wired.

- [ ] **Step 3: Update report filter parsing**

In `core/reports.py`, include these keys in the filter dictionary built from `request.GET`:

```python
        'approval_status': request.GET.get('approval_status', ''),
        'project_progress': request.GET.get('project_progress', ''),
        'department': request.GET.get('department', ''),
        'submitter_type': request.GET.get('submitter_type', ''),
```

Apply filters to `proposals` after existing status/type filtering:

```python
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
```

Add these context values:

```python
        'approval_status_choices': ProposalStatus.choices,
        'project_progress_choices': ProjectProgressStatus.choices,
        'department_choices': CustomUser.DEPARTMENT_CHOICES,
        'submitter_type_choices': [
            ('faculty_direct', 'Faculty Direct Submission'),
            ('staff_on_behalf', 'Staff on Behalf of Faculty'),
        ],
```

Add imports:

```python
from proposals.models import Proposal, ProposalType, ProposalStatus, ProjectProgressStatus
from users.models import CustomUser
```

- [ ] **Step 4: Update report template filters**

In `templates/core/comprehensive_reports.html`, add select controls inside the existing report filter form:

```django
<select name="approval_status" class="rounded-lg border border-slate-300 px-3 py-2 text-sm">
    <option value="">All approval statuses</option>
    {% for value, label in approval_status_choices %}
    <option value="{{ value }}" {% if filters.approval_status == value %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
</select>

<select name="project_progress" class="rounded-lg border border-slate-300 px-3 py-2 text-sm">
    <option value="">All project progress</option>
    {% for value, label in project_progress_choices %}
    <option value="{{ value }}" {% if filters.project_progress == value %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
</select>

<select name="department" class="rounded-lg border border-slate-300 px-3 py-2 text-sm">
    <option value="">All departments</option>
    {% for value, label in department_choices %}
    <option value="{{ value }}" {% if filters.department == value %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
</select>

<select name="submitter_type" class="rounded-lg border border-slate-300 px-3 py-2 text-sm">
    <option value="">All submitter types</option>
    {% for value, label in submitter_type_choices %}
    <option value="{{ value }}" {% if filters.submitter_type == value %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
</select>
```

- [ ] **Step 5: Preserve filters in PDF links**

Where the PDF export query string is built, include:

```django
{% if filters.approval_status %}&approval_status={{ filters.approval_status }}{% endif %}
{% if filters.project_progress %}&project_progress={{ filters.project_progress }}{% endif %}
{% if filters.department %}&department={{ filters.department }}{% endif %}
{% if filters.submitter_type %}&submitter_type={{ filters.submitter_type }}{% endif %}
```

- [ ] **Step 6: Run report tests to verify they pass**

Run: `python manage.py test core.tests_reports`

Expected: PASS.

- [ ] **Step 7: Commit Task 6**

Run:

```bash
git add core/reports.py templates/core/comprehensive_reports.html core/tests_reports.py
git commit -m "feat: add proposal workflow report filters"
```

---

### Task 7: Full Regression and Migration Check

**Files:**
- Modify files only if a command below exposes a concrete failure.

- [ ] **Step 1: Run Django system checks**

Run: `python manage.py check`

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 2: Run migrations in check mode**

Run: `python manage.py makemigrations --check --dry-run`

Expected: `No changes detected`.

- [ ] **Step 3: Run full test suite**

Run: `python manage.py test`

Expected: all tests pass.

- [ ] **Step 4: Inspect final git status**

Run: `git status --short`

Expected: only intentional tracked changes from the implementation branch are present. The pre-existing `db.sqlite3` modification may remain if it was present before starting this work.

- [ ] **Step 5: Commit verification fixes if any were needed**

If Step 1, Step 2, or Step 3 required fixes, commit those fixes:

```bash
git add users proposals portal core templates
git commit -m "test: stabilize proposal workflow regression suite"
```

---

## Self-Review Notes

- Spec coverage: Tasks cover role merge, staff-on-behalf submission, staff recommendation, admin gating, resubmission back to staff, project progress, dashboard, notifications, and report filters.
- Placeholder scan: No placeholder markers or deferred sections remain in the plan.
- Type consistency: The plan consistently uses `RESEARCH_EXTENSION_STAFF`, `PENDING_RECOMMENDATION`, `RECOMMENDED_APPROVAL`, `RECOMMENDED_REVISION`, `APPROVED`, `REJECTED`, `ONGOING`, `PRESENTED`, and `COMPLETED`.
