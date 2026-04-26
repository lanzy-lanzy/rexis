from datetime import date, datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from extension.models import ExtensionRecord, ExtensionStatus
from proposals.models import Proposal, ProposalStatus, ProposalType
from research.models import ResearchRecord, ResearchStatus
from users.models import CustomUser, UserRole


class ComprehensiveReportsTests(TestCase):
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
            first_name='Faith',
            last_name='Faculty',
        )
        self.other_faculty = CustomUser.objects.create_user(
            username='other',
            password='password',
            role=UserRole.FACULTY,
        )
        self.research_staff = CustomUser.objects.create_user(
            username='researcher',
            password='password',
            role=UserRole.RESEARCH_STAFF,
        )
        self.extension_staff = CustomUser.objects.create_user(
            username='extension',
            password='password',
            role=UserRole.EXTENSION_STAFF,
        )

        self.faculty_proposal = Proposal.objects.create(
            title='Faculty Water Quality Study',
            abstract='Research abstract',
            full_description='Full description',
            proposal_type=ProposalType.RESEARCH,
            faculty_author=self.faculty,
            status=ProposalStatus.APPROVED,
        )
        self.other_proposal = Proposal.objects.create(
            title='Other Faculty Proposal',
            abstract='Other abstract',
            full_description='Other description',
            proposal_type=ProposalType.EXTENSION,
            faculty_author=self.other_faculty,
            status=ProposalStatus.PENDING,
        )
        self.research_record = ResearchRecord.objects.create(
            proposal=self.faculty_proposal,
            lead_researcher=self.research_staff,
            status=ResearchStatus.ONGOING,
            start_date=date(2026, 1, 15),
            funding_source='College Fund',
            funding_amount=25000,
        )
        self.research_record.co_researchers.add(self.faculty)
        self.extension_record = ExtensionRecord.objects.create(
            proposal=self.other_proposal,
            title='Barangay Skills Training',
            coordinator=self.extension_staff,
            location='San Miguel',
            status=ExtensionStatus.ONGOING,
            start_date=date(2026, 2, 1),
            beneficiary_count=40,
        )
        self.extension_record.team_members.add(self.faculty)

        Proposal.objects.filter(pk=self.faculty_proposal.pk).update(
            date_submitted=timezone.make_aware(datetime(2026, 1, 15, 9, 0))
        )
        Proposal.objects.filter(pk=self.other_proposal.pk).update(
            date_submitted=timezone.make_aware(datetime(2026, 2, 10, 9, 0))
        )

    def test_reports_page_is_available_from_sidebar(self):
        self.client.login(username='faculty', password='password')

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, reverse('comprehensive_reports'))
        self.assertContains(response, 'Reports')

    def test_faculty_report_is_scoped_to_owned_and_participating_records(self):
        self.client.login(username='faculty', password='password')

        response = self.client.get(reverse('comprehensive_reports'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Faculty Water Quality Study')
        self.assertContains(response, 'Barangay Skills Training')
        self.assertNotContains(response, 'Other Faculty Proposal')

    def test_admin_report_includes_institution_wide_records(self):
        self.client.login(username='admin', password='password')

        response = self.client.get(reverse('comprehensive_reports'))

        self.assertContains(response, 'Faculty Water Quality Study')
        self.assertContains(response, 'Other Faculty Proposal')
        self.assertContains(response, 'Barangay Skills Training')

    def test_pdf_export_returns_pdf_attachment(self):
        self.client.login(username='admin', password='password')

        response = self.client.get(reverse('comprehensive_reports_pdf'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_search_filters_all_report_sections(self):
        self.client.login(username='admin', password='password')

        response = self.client.get(reverse('comprehensive_reports'), {'q': 'Water'})

        self.assertContains(response, 'Faculty Water Quality Study')
        self.assertNotContains(response, 'Other Faculty Proposal')
        self.assertNotContains(response, 'Barangay Skills Training')
        self.assertContains(response, 'value="Water"')

    def test_type_and_status_filters_work_together(self):
        self.client.login(username='admin', password='password')

        response = self.client.get(
            reverse('comprehensive_reports'),
            {'record_type': 'extension', 'status': ExtensionStatus.ONGOING},
        )

        self.assertContains(response, 'Barangay Skills Training')
        self.assertNotContains(response, 'Faculty Water Quality Study')
        self.assertNotContains(response, 'Other Faculty Proposal')

    def test_date_range_filters_by_relevant_record_dates(self):
        self.client.login(username='admin', password='password')

        response = self.client.get(
            reverse('comprehensive_reports'),
            {'start_date': '2026-02-01', 'end_date': '2026-02-28'},
        )

        self.assertContains(response, 'Other Faculty Proposal')
        self.assertContains(response, 'Barangay Skills Training')
        self.assertNotContains(response, 'Faculty Water Quality Study')
        self.assertContains(response, 'value="2026-02-01"')
        self.assertContains(response, 'value="2026-02-28"')

    def test_pdf_export_link_preserves_report_filters(self):
        self.client.login(username='admin', password='password')

        response = self.client.get(
            reverse('comprehensive_reports'),
            {'q': 'Barangay', 'record_type': 'extension', 'start_date': '2026-02-01'},
        )

        self.assertContains(response, 'q=Barangay')
        self.assertContains(response, 'record_type=extension')
        self.assertContains(response, 'start_date=2026-02-01')
