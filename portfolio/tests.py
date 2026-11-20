import json
from io import StringIO
from unittest.mock import patch

import httpx
from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class PortfolioViewsTests(TestCase):
    def test_homepage_renders_portfolio_content(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Making resilient")
        self.assertContains(response, "100k+")
        self.assertContains(response, "MISSION")

    def test_homepage_includes_smalltalk_launcher(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Personal Assistant")
        self.assertContains(response, "Qwen3.5:0.8b")
        self.assertContains(response, "professional background")
        self.assertContains(response, reverse("smalltalk_chat"))

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

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_uses_configured_model_options(self, client_factory):
        client = client_factory.return_value
        client.chat.return_value = {"message": {"content": "Hello back"}}
        messages = [{"role": "user", "content": "Hello"}]
        profile = {"name": "Test Profile", "skills": ["Python"]}

        with patch("pathlib.Path.open", return_value=StringIO(json.dumps(profile))):
            response = self.client.post(
                reverse("smalltalk_chat"),
                data=json.dumps({"messages": messages}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "Hello back"})
        client_factory.assert_called_once_with(host="http://127.0.0.1:11434")
        sent_messages = client.chat.call_args.kwargs["messages"]
        self.assertEqual(sent_messages[0]["role"], "system")
        self.assertIn("Respond briefly and warmly to simple social small talk", sent_messages[0]["content"])
        self.assertIn("Never use outside knowledge", sent_messages[0]["content"])
        self.assertIn(json.dumps(profile), sent_messages[0]["content"])
        self.assertEqual(sent_messages[1:], messages)
        client.chat.assert_called_once_with(
            model="qwen3.5:0.8b",
            messages=sent_messages,
            think=False,
            stream=False,
            keep_alive=-1,
            options={"temperature": 0.2, "num_predict": 128, "num_ctx": 4096},
        )

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_is_unavailable_without_profile(self, client_factory):
        with patch("pathlib.Path.open", side_effect=FileNotFoundError):
            response = self.client.post(
                reverse("smalltalk_chat"),
                data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 503)
        client_factory.assert_not_called()

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_rejects_invalid_messages(self, client_factory):
        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": [], "content": "Hello"}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        client_factory.assert_not_called()

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_rejects_oversized_context(self, client_factory):
        oversized_contexts = [
            [{"role": "user", "content": "Hi"}] * 9,
            [{"role": "user", "content": "x" * 1001}],
        ]

        for messages in oversized_contexts:
            with self.subTest(message_count=len(messages), content_length=len(messages[-1]["content"])):
                response = self.client.post(
                    reverse("smalltalk_chat"),
                    data=json.dumps({"messages": messages}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)

        client_factory.assert_not_called()

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_reports_unavailable_ollama(self, client_factory):
        client_factory.return_value.chat.side_effect = httpx.ConnectError("offline")

        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": "The personal assistant is temporarily unavailable. Please try again later."},
        )

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_reports_invalid_ollama_response(self, client_factory):
        client_factory.return_value.chat.return_value = {"message": {}}

        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {"error": "The personal assistant couldn't generate a reply. Please try again."},
        )

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_reports_unexpected_ollama_failure(self, client_factory):
        client_factory.return_value.chat.side_effect = RuntimeError("unexpected client failure")

        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"error": "The personal assistant is temporarily unavailable. Please try again later."},
        )
