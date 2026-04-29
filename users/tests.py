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
