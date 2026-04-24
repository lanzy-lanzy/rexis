from django.test import TestCase
from django.urls import reverse


class BrandingTests(TestCase):
    def test_home_uses_new_brand_name_and_logo(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Research &amp; Extension (MIS)')
        self.assertContains(response, '/static/images/jh_logo.png')
        self.assertNotContains(response, '>REXIS<')
        self.assertNotContains(response, 'About REXIS')

    def test_login_uses_new_brand_name_and_logo(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, 'Research &amp; Extension (MIS)')
        self.assertContains(response, '/static/images/jh_logo.png')
        self.assertNotContains(response, '>REXIS<')
