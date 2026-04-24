import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import CustomUser, UserRole

from . import models as proposal_models
from .models import Proposal, ProposalStatus, ProposalType


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

    def test_admin_rejection_stores_missing_requirements(self):
        self.get_requirement_model()
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
        self.assertEqual(self.proposal.status, ProposalStatus.PENDING)
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
        self.assertEqual(self.proposal.status, ProposalStatus.PENDING)
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
        self.proposal.status = ProposalStatus.PENDING
        self.proposal.save()
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
