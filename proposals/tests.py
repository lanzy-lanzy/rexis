import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from users.models import CustomUser, UserRole

from . import models as proposal_models
from .models import (
    Proposal,
    ProposalStatus,
    ProposalType,
    ProposalRequirement,
    ProjectProgressStatus,
    ProposalTrackingEvent,
    ProposalTrackingEventType,
)


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
        self.staff = CustomUser.objects.create_user(
            username='staff',
            password='password',
            role=UserRole.RESEARCH_EXTENSION_STAFF,
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
            status=ProposalStatus.PENDING_RECOMMENDATION,
        )

    def get_requirement_model(self):
        requirement_model = getattr(proposal_models, 'ProposalRequirement', None)
        self.assertIsNotNone(requirement_model, 'ProposalRequirement model should exist')
        return requirement_model

    def test_admin_rejection_stores_missing_requirements(self):
        self.get_requirement_model()
        self.client.login(username='staff', password='password')
        self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {'status': ProposalStatus.RECOMMENDED_APPROVAL, 'recommendation_notes': 'Good'},
        )
        self.client.logout()
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
        self.client.login(username='staff', password='password')
        self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {'status': ProposalStatus.RECOMMENDED_APPROVAL, 'recommendation_notes': 'Good'},
        )
        self.client.logout()
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
        self.client.login(username='staff', password='password')
        self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {'status': ProposalStatus.RECOMMENDED_APPROVAL, 'recommendation_notes': 'Good'},
        )
        self.client.logout()
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
        self.client.login(username='staff', password='password')
        self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {'status': ProposalStatus.RECOMMENDED_APPROVAL, 'recommendation_notes': 'Good'},
        )
        self.client.logout()
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.RECOMMENDED_APPROVAL)
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
            'project_status': ProjectProgressStatus.ONGOING,
            'research_staff': '',
            'proposal_document': SimpleUploadedFile(
                'proposal.pdf',
                b'%PDF-1.4 proposal',
                content_type='application/pdf',
            ),
            'budget_pdf': SimpleUploadedFile(
                'budget.pdf',
                b'%PDF-1.4 budget',
                content_type='application/pdf',
            ),
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
        self.assertEqual(created.project_progress_status, ProjectProgressStatus.ONGOING)
        self.assertTrue(
            created.tracking_events.filter(
                event_type=ProposalTrackingEventType.SUBMITTED,
                title='Proposal submitted',
            ).exists()
        )
        self.assertTrue(
            created.tracking_events.filter(
                event_type=ProposalTrackingEventType.DOCUMENTS_UPLOADED,
                description__icontains='Proposal Document',
            ).exists()
        )

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

    def test_presented_submission_does_not_require_full_description(self):
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.post(
            reverse('proposal_create'),
            self.proposal_payload(
                project_status=ProjectProgressStatus.PRESENTED,
                full_description='',
                proposal_document='',
                budget_pdf='',
                certificate_of_appearance=SimpleUploadedFile(
                    'appearance.pdf',
                    b'%PDF-1.4 appearance',
                    content_type='application/pdf',
                ),
                certificate_of_participation=SimpleUploadedFile(
                    'participation.pdf',
                    b'%PDF-1.4 participation',
                    content_type='application/pdf',
                ),
                abstract_document=SimpleUploadedFile(
                    'abstract.pdf',
                    b'%PDF-1.4 abstract',
                    content_type='application/pdf',
                ),
                conference_proceedings=SimpleUploadedFile(
                    'proceedings.pdf',
                    b'%PDF-1.4 proceedings',
                    content_type='application/pdf',
                ),
            ),
        )

        created = Proposal.objects.get(title='Submitted Workflow Proposal')
        self.assertRedirects(response, reverse('proposal_list'))
        self.assertEqual(created.project_progress_status, ProjectProgressStatus.PRESENTED)
        self.assertEqual(created.full_description, '')

    def test_ongoing_submission_requires_full_description(self):
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.post(
            reverse('proposal_create'),
            self.proposal_payload(full_description=''),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Full description is required for Ongoing status.')
        self.assertFalse(Proposal.objects.filter(title='Submitted Workflow Proposal').exists())

    def test_admin_cannot_review_before_staff_recommendation(self):
        self.client.login(username='workflow-admin', password='password')

        response = self.client.get(reverse('proposal_review', args=[self.proposal.pk]))

        self.assertRedirects(response, reverse('proposal_detail', args=[self.proposal.pk]))

    def test_staff_detail_page_shows_recommend_action_for_pending_proposal(self):
        self.client.login(username='workflow-staff-view', password='password')
        ProposalTrackingEvent.objects.create(
            proposal=self.proposal,
            event_type=ProposalTrackingEventType.SUBMITTED,
            title='Proposal submitted',
            status=ProposalStatus.PENDING_RECOMMENDATION,
            actor=self.faculty,
        )

        response = self.client.get(reverse('proposal_detail', args=[self.proposal.pk]))

        self.assertContains(response, 'Review & Recommend')
        self.assertContains(response, reverse('proposal_recommend', args=[self.proposal.pk]))
        self.assertContains(response, 'Proposal Tracking')
        self.assertContains(response, 'Proposal submitted')

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
        self.assertTrue(
            self.proposal.tracking_events.filter(
                event_type=ProposalTrackingEventType.RECOMMENDED_APPROVAL,
                title='Recommended for admin approval',
            ).exists()
        )

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

    def test_staff_revision_requires_missing_requirements(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.RECOMMENDED_REVISION,
                'recommendation_notes': 'Please resubmit the lacking documents.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select at least one missing requirement')
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.PENDING_RECOMMENDATION)
        self.assertEqual(self.proposal.requirements.count(), 0)

    def test_staff_recommendation_page_shows_all_submitted_documents_with_preview(self):
        self.proposal.project_progress_status = ProjectProgressStatus.PRESENTED
        self.proposal.proposal_document.name = 'proposals/documents/main-proposal.pdf'
        self.proposal.budget_pdf.name = 'proposals/budgets/project-budget.pdf'
        self.proposal.abstract_document.name = 'proposals/abstracts/abstract.pdf'
        self.proposal.certificate_of_appearance.name = 'proposals/certificates/appearance.pdf'
        self.proposal.certificate_of_participation.name = 'proposals/certificates/participation.pdf'
        self.proposal.conference_proceedings.name = 'proposals/proceedings/proceedings.pdf'
        self.proposal.save()
        ProposalTrackingEvent.objects.create(
            proposal=self.proposal,
            event_type=ProposalTrackingEventType.DOCUMENTS_UPLOADED,
            title='Submission documents uploaded',
            description='Presented project documents uploaded.',
            status=ProposalStatus.PENDING_RECOMMENDATION,
            actor=self.faculty,
        )
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_recommend', args=[self.proposal.pk]))

        self.assertContains(response, 'All Proposal Documents')
        self.assertContains(response, 'Preview Proposal document')
        self.assertContains(response, 'Preview Budget file')
        self.assertContains(response, 'Preview Abstract document')
        self.assertContains(response, 'Preview Certificate of appearance')
        self.assertContains(response, 'Preview Certificate of participation')
        self.assertContains(response, 'Preview Conference proceedings')
        self.assertContains(response, 'universalDocumentPreview')
        self.assertIn('document_versions', response.context)
        self.assertIn('tracking_events', response.context)
        self.assertIn('document_statuses', response.context)

    def test_faculty_uploaded_documents_are_available_in_staff_detail_context(self):
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.post(
            reverse('proposal_create'),
            self.proposal_payload(
                project_status=ProjectProgressStatus.PUBLISHED,
                full_description='',
                proposal_document='',
                budget_pdf='',
                full_paper=SimpleUploadedFile(
                    'full-paper.pdf',
                    b'%PDF-1.4 full paper',
                    content_type='application/pdf',
                ),
                certificate_of_publication=SimpleUploadedFile(
                    'publication-certificate.pdf',
                    b'%PDF-1.4 certificate',
                    content_type='application/pdf',
                ),
            ),
        )

        self.assertRedirects(response, reverse('proposal_list'))
        proposal = Proposal.objects.get(title='Submitted Workflow Proposal')
        self.client.logout()
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_detail', args=[proposal.pk]))

        self.assertContains(response, 'All Proposal Documents')
        self.assertContains(response, 'Preview Full paper')
        self.assertContains(response, 'Preview Certificate of publication')
        self.assertIn('document_statuses', response.context)

    def test_staff_detail_hides_submission_narrative_for_presented_proposal(self):
        self.proposal.project_progress_status = ProjectProgressStatus.PRESENTED
        self.proposal.abstract = 'Submission-only abstract should not appear for presented work.'
        self.proposal.full_description = 'Submission-only full description should not appear for presented work.'
        self.proposal.save()
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_detail', args=[self.proposal.pk]))

        self.assertContains(response, 'Presented')
        self.assertContains(response, 'All Proposal Documents')
        self.assertNotContains(response, 'Submission-only abstract should not appear for presented work.')
        self.assertNotContains(response, 'Submission-only full description should not appear for presented work.')
        self.assertNotContains(response, '>Abstract<', html=False)
        self.assertNotContains(response, '>Full Description<', html=False)

    def test_faculty_detail_hides_submission_narrative_for_published_proposal(self):
        self.proposal.project_progress_status = ProjectProgressStatus.PUBLISHED
        self.proposal.abstract = 'Submission-only abstract should not appear for published work.'
        self.proposal.full_description = 'Submission-only full description should not appear for published work.'
        self.proposal.save()
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.get(reverse('proposal_detail', args=[self.proposal.pk]))

        self.assertContains(response, 'Published')
        self.assertContains(response, 'All Proposal Documents')
        self.assertNotContains(response, 'Submission-only abstract should not appear for published work.')
        self.assertNotContains(response, 'Submission-only full description should not appear for published work.')
        self.assertNotContains(response, '>Abstract<', html=False)
        self.assertNotContains(response, '>Full Description<', html=False)

    def test_staff_revision_stores_missing_requirements_for_resubmission(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.post(
            reverse('proposal_recommend', args=[self.proposal.pk]),
            {
                'status': ProposalStatus.RECOMMENDED_REVISION,
                'recommendation_notes': 'Please upload the workplan and MOA.',
                'missing_requirements': ['workplan', 'moa'],
                'custom_requirements': 'Signed department endorsement',
            },
        )

        self.assertRedirects(response, reverse('proposal_list'))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, ProposalStatus.RECOMMENDED_REVISION)
        self.assertEqual(self.proposal.recommended_by, self.staff)
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
                ('workplan', 'Workplan', False),
                ('moa', 'MOA', False),
                ('custom_1', 'Signed department endorsement', True),
            ],
        )

    def test_faculty_sees_upload_fields_for_staff_recommended_revision(self):
        self.proposal.status = ProposalStatus.RECOMMENDED_REVISION
        self.proposal.recommendation_notes = 'Please upload the missing workplan.'
        self.proposal.save()
        ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='workplan',
            label='Workplan',
        )
        self.client.login(username='workflow-faculty-view', password='password')

        response = self.client.get(reverse('proposal_detail', args=[self.proposal.pk]))

        self.assertContains(response, 'Upload Requested Documents')
        self.assertContains(response, 'Workplan')

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
        self.assertTrue(
            self.proposal.tracking_events.filter(
                event_type=ProposalTrackingEventType.ADMIN_APPROVED,
                title='Approved by admin',
            ).exists()
        )

    def test_staff_can_filter_admin_approved_proposals(self):
        self.proposal.status = ProposalStatus.APPROVED
        self.proposal.reviewed_by = self.admin
        self.proposal.reviewed_at = timezone.now()
        self.proposal.save()
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_list'), {'status': ProposalStatus.APPROVED})

        self.assertContains(response, 'Two Stage Review Proposal')
        self.assertContains(response, 'Approved by Admin')

    def test_staff_can_filter_proposals_by_project_progress_status(self):
        self.proposal.status = ProposalStatus.APPROVED
        self.proposal.project_progress_status = ProjectProgressStatus.ONGOING
        self.proposal.save()
        Proposal.objects.create(
            title='Published Faculty Work',
            abstract='This published work should not appear in the ongoing project filter.',
            full_description='Published project description.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            submitted_by=self.faculty,
            status=ProposalStatus.APPROVED,
            project_progress_status=ProjectProgressStatus.PUBLISHED,
        )
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(
            reverse('proposal_list'),
            {
                'status': ProposalStatus.APPROVED,
                'progress_status': ProjectProgressStatus.ONGOING,
            },
        )

        self.assertContains(response, 'Two Stage Review Proposal')
        self.assertContains(response, 'Ongoing')
        self.assertNotContains(response, 'Published Faculty Work')

    def test_staff_sidebar_contains_project_status_navigation(self):
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_list'))

        self.assertContains(response, 'Project Status')
        self.assertContains(response, 'progress_status=ONGOING')
        self.assertContains(response, 'progress_status=COMPLETED')
        self.assertContains(response, 'progress_status=PRESENTED')
        self.assertContains(response, 'progress_status=PUBLISHED')

    def test_tracking_dashboard_shows_document_status_and_latest_event(self):
        self.proposal.status = ProposalStatus.APPROVED
        self.proposal.project_progress_status = ProjectProgressStatus.ONGOING
        self.proposal.proposal_document.name = 'proposals/documents/trackable-proposal.pdf'
        self.proposal.save()
        ProposalTrackingEvent.objects.create(
            proposal=self.proposal,
            event_type=ProposalTrackingEventType.ADMIN_APPROVED,
            title='Approved by admin',
            status=ProposalStatus.APPROVED,
            actor=self.admin,
        )
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(reverse('proposal_tracking_dashboard'))

        self.assertContains(response, 'Document Tracking')
        self.assertContains(response, 'Two Stage Review Proposal')
        self.assertContains(response, 'Approved by Admin')
        self.assertContains(response, 'Proposal document')
        self.assertContains(response, 'Budget file')
        self.assertContains(response, 'Uploaded')
        self.assertContains(response, 'Missing')
        self.assertContains(response, 'Approved by admin')

    def test_tracking_dashboard_searches_document_filename(self):
        self.proposal.project_progress_status = ProjectProgressStatus.ONGOING
        self.proposal.proposal_document.name = 'proposals/documents/trackable-proposal.pdf'
        self.proposal.save()
        Proposal.objects.create(
            title='Different Faculty Proposal',
            abstract='This proposal should not appear in the document filename search.',
            full_description='Different proposal description.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            submitted_by=self.faculty,
            project_progress_status=ProjectProgressStatus.ONGOING,
        )
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(
            reverse('proposal_tracking_dashboard'),
            {'search': 'trackable-proposal.pdf'},
        )

        self.assertContains(response, 'Two Stage Review Proposal')
        self.assertNotContains(response, 'Different Faculty Proposal')

    def test_tracking_dashboard_filters_missing_required_documents(self):
        complete_proposal = Proposal.objects.create(
            title='Complete Tracking Proposal',
            abstract='This proposal has all required tracking documents.',
            full_description='Complete proposal description.',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            submitted_by=self.faculty,
            project_progress_status=ProjectProgressStatus.ONGOING,
        )
        complete_proposal.proposal_document.name = 'proposals/documents/complete.pdf'
        complete_proposal.budget_pdf.name = 'proposals/budgets/complete-budget.pdf'
        complete_proposal.save()
        self.proposal.project_progress_status = ProjectProgressStatus.ONGOING
        self.proposal.proposal_document.name = 'proposals/documents/incomplete.pdf'
        self.proposal.save()
        ProposalRequirement.objects.create(
            proposal=self.proposal,
            requirement_key='workplan',
            label='Workplan',
        )
        self.client.login(username='workflow-staff-view', password='password')

        response = self.client.get(
            reverse('proposal_tracking_dashboard'),
            {'document_status': 'missing'},
        )

        self.assertContains(response, 'Two Stage Review Proposal')
        self.assertContains(response, 'Workplan')
        self.assertNotContains(response, 'Complete Tracking Proposal')

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
        self.assertTrue(
            self.proposal.tracking_events.filter(
                event_type=ProposalTrackingEventType.RESUBMITTED,
                title='Requested documents resubmitted',
            ).exists()
        )
