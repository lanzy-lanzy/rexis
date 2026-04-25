from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser, UserRole


class DashboardVisualRefreshTests(TestCase):
    def make_user(self, username, role):
        return CustomUser.objects.create_user(
            username=username,
            password='password123',
            role=role,
        )

    def assert_dashboard_shell(self, user, expected_heading):
        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-sidebar-variant="executive-clean"')
        self.assertContains(response, 'data-dashboard-shell')
        self.assertContains(response, 'data-dashboard-variant="executive-clean"')
        self.assertContains(response, expected_heading)
        self.assertContains(response, 'Operational summary')
        self.assertContains(response, 'metric-card')

    def test_admin_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('admin-user', UserRole.ADMIN)

        self.assert_dashboard_shell(user, 'Admin Workspace')

    def test_faculty_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('faculty-user', UserRole.FACULTY)

        self.assert_dashboard_shell(user, 'Faculty Workspace')

    def test_research_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('research-user', UserRole.RESEARCH_STAFF)

        self.assert_dashboard_shell(user, 'Research Workspace')

    def test_extension_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('extension-user', UserRole.EXTENSION_STAFF)

        self.assert_dashboard_shell(user, 'Extension Workspace')
