import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from users.models import CustomUser, UserRole

from . import models as proposal_models
from .models import Proposal, ProposalRequirement, ProposalStatus, ProposalType


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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProposalRejectionResubmissionTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='password',
            role=UserRole.ADMIN,
        )
        self.faculty = CustomUser.objects.create_user(
            username='faculty',
            password='password',
            role=UserRole.FACULTY,
        )
        self.other_faculty = CustomUser.objects.create_user(
            username='other-faculty',
            password='password',
            role=UserRole.FACULTY,
        )
        self.staff = CustomUser.objects.create_user(
            username='resubmission-staff',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
        )
        self.proposal = Proposal.objects.create(
            title='Community Research Proposal',
            abstract='This proposal abstract has enough detail for review and testing.',
            full_description='Full description for a proposal that will be reviewed.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
        )

    def get_requirement_model(self):
        requirement_model = getattr(proposal_models, 'ProposalRequirement', None)
        self.assertIsNotNone(requirement_model, 'ProposalRequirement model should exist')
        return requirement_model

    def prepare_for_admin_review(self):
        self.proposal.status = ProposalStatus.RECOMMENDED_APPROVAL
        self.proposal.recommended_by = self.staff
        self.proposal.recommended_at = timezone.now()
        self.proposal.save()

    def test_admin_rejection_stores_missing_requirements(self):
        self.get_requirement_model()
        self.prepare_for_admin_review()
        self.client.login(username='admin', password='password')

        response = self.client.post(
            reverse('proposal_review', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.REJECTED,
                'review_notes': 'Please upload the missing budget letter and MOA.',
                'missing_requirements': ['budget_pdf', 'moa'],
                'custom_requirements': 'Signed endorsement letter',
            },
        )

        self.assertRedirects(response, reverse('proposal_list'))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.REJECTED)

        requirements = list(
            self.proposal.requirements.order_by('created_at').values_list(
                'requirement_key',
                'label',
                'is_custom',
            )
        )
        self.assertEqual(
            requirements,
            [
                ('budget_pdf', 'Budget Letter or Budget PDF', False),
                ('moa', 'MOA', False),
                ('custom_1', 'Signed endorsement letter', True),
            ],
        )

    def test_rejection_requires_at_least_one_missing_requirement(self):
        self.get_requirement_model()
        self.prepare_for_admin_review()
        self.client.login(username='admin', password='password')

        response = self.client.post(
            reverse('proposal_review', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.REJECTED,
                'review_notes': 'Please complete the missing documents.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select at least one missing requirement')
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.RECOMMENDED_APPROVAL)
        self.assertEqual(self.proposal.requirements.count(), 0)

    def test_faculty_author_can_resubmit_rejected_proposal_files(self):
        ProposalRequirement = self.get_requirement_model()
        self.proposal.status = ProposalStatus.REJECTED
        self.proposal.review_notes = 'Upload the missing budget document.'
        self.proposal.save()
        requirement = ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='budget_pdf',
            label='Budget Letter or Budget PDF',
        )
        self.client.login(username='faculty', password='password')

        upload = SimpleUploadedFile(
            'budget.pdf',
            b'%PDF-1.4 budget document',
            content_type='application/pdf',
        )
        response = self.client.post(
            reverse('proposal_resubmit', args=[self.proposal.pk]),
            {f'requirement_{requirement.pk}': upload},
        )

        self.assertRedirects(response, reverse('proposal_detail', args=[self.proposal.pk]))
        self.proposal.refresh_from_db()
        requirement.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.PENDING_RECOMMENDATION)
        self.assertTrue(requirement.is_resubmitted)
        self.assertTrue(requirement.uploaded_file.name)
        self.assertTrue(self.proposal.budget_pdf.name)

    def test_non_author_cannot_resubmit_rejected_proposal(self):
        ProposalRequirement = self.get_requirement_model()
        self.proposal.status = ProposalStatus.REJECTED
        self.proposal.save()
        requirement = ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='moa',
            label='MOA',
        )
        self.client.login(username='other-faculty', password='password')

        response = self.client.post(
            reverse('proposal_resubmit', args=[self.proposal.pk]),
            {
                f'requirement_{requirement.pk}': SimpleUploadedFile(
                    'moa.pdf',
                    b'%PDF-1.4 moa',
                    content_type='application/pdf',
                ),
            },
        )

        self.assertRedirects(response, reverse('proposal_list'))
        self.proposal.refresh_from_db()
        requirement.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.REJECTED)
        self.assertFalse(requirement.is_resubmitted)

    def test_approval_after_resubmission_preserves_requirement_history(self):
        ProposalRequirement = self.get_requirement_model()
        self.prepare_for_admin_review()
        requirement = ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='budget_pdf',
            label='Budget Letter or Budget PDF',
            uploaded_file=SimpleUploadedFile(
                'budget.pdf',
                b'%PDF-1.4 budget',
                content_type='application/pdf',
            ),
            uploaded_at='2026-04-24T00:00:00Z',
            is_resubmitted=True,
        )
        self.client.login(username='admin', password='password')

        response = self.client.post(
            reverse('proposal_review', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.APPROVED,
                'review_notes': 'Approved after resubmission.',
            },
        )

        self.assertRedirects(response, reverse('proposal_list'))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.APPROVED)
        self.assertTrue(ProposalRequirement.objects.filter(pk=requirement.pk).exists())

    def test_admin_review_page_shows_document_previews_before_approval(self):
        ProposalRequirement = self.get_requirement_model()
        self.prepare_for_admin_review()
        self.proposal.proposal_document = SimpleUploadedFile(
            'proposal.pdf',
            b'%PDF-1.4 proposal',
            content_type='application/pdf',
        )
        self.proposal.budget_pdf = SimpleUploadedFile(
            'budget.pdf',
            b'%PDF-1.4 budget',
            content_type='application/pdf',
        )
        self.proposal.save()
        ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='moa',
            label='MOA',
            uploaded_file=SimpleUploadedFile(
                'moa.pdf',
                b'%PDF-1.4 moa',
                content_type='application/pdf',
            ),
            is_resubmitted=True,
        )
        self.client.login(username='admin', password='password')

        response = self.client.get(reverse('proposal_review', args=[self.proposal.pk]))

        self.assertContains(response, 'Documents for Review')
        self.assertContains(response, 'Preview Proposal Document')
        self.assertContains(response, 'Preview Budget PDF')
        self.assertContains(response, 'Preview MOA')
