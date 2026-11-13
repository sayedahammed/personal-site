from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class PortfolioViewsTests(TestCase):
    def test_homepage_renders_portfolio_content(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Making complex")
        self.assertContains(response, "100k+")
        self.assertContains(response, "MISSION")

    def test_valid_contact_message_is_saved(self):
        response = self.client.post(
            reverse("contact"),
            {
                "name": "A. Visitor",
                "email": "visitor@example.com",
                "subject": "Project inquiry",
                "message": "I would like to discuss a project.",
            },
        )

        self.assertRedirects(response, f"{reverse('home')}#contact")
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_invalid_contact_message_is_not_saved(self):
        response = self.client.post(
            reverse("contact"),
            {
                "name": "A. Visitor",
                "email": "not-an-email",
                "subject": "Project inquiry",
                "message": "I would like to discuss a project.",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address.", status_code=400)

    def test_resume_download_returns_pdf_attachment(self):
        response = self.client.get(reverse("download_resume"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(next(iter(response.streaming_content)).startswith(b"%PDF"))
