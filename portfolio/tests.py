import json
from io import StringIO
from unittest.mock import patch

import httpx
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class PortfolioViewsTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_homepage_renders_portfolio_content(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Making complex")
        self.assertContains(response, "100k+")
        self.assertContains(response, "MISSION")

    def test_homepage_includes_smalltalk_launcher(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "AI Assistant")
        self.assertContains(response, "qwen3:1.7b")
        self.assertContains(response, "professional background")
        self.assertContains(response, reverse("smalltalk_chat"))

    def test_homepage_displays_configured_ollama_model(self):
        with self.settings(OLLAMA_MODEL="llama3.2"):
            response = self.client.get(reverse("home"))

        self.assertContains(response, "Powered by llama3.2")

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
        client.chat.return_value = iter([
            {"message": {"content": "Hello"}},
            {"message": {"content": " back"}},
        ])
        messages = [{"role": "user", "content": "Hello"}]
        profile = {"name": "Test Profile", "skills": ["Python"]}

        with (
            self.settings(OLLAMA_MODEL="test-model"),
            patch("pathlib.Path.open", return_value=StringIO(json.dumps(profile))),
        ):
            response = self.client.post(
                reverse("smalltalk_chat"),
                data=json.dumps({"messages": messages}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        stream_output = b"".join(response.streaming_content).decode()
        self.assertIn("Hello".encode("utf-8").hex(), stream_output)
        self.assertIn(" back".encode("utf-8").hex(), stream_output)
        self.assertIn("event: done", stream_output)
        client_factory.assert_called_once_with(host="http://127.0.0.1:11434")
        sent_messages = client.chat.call_args.kwargs["messages"]
        self.assertEqual(sent_messages[0]["role"], "system")
        self.assertIn("Respond briefly and warmly to simple social small talk", sent_messages[0]["content"])
        self.assertIn("medium-length answer of 4-6 sentences", sent_messages[0]["content"])
        self.assertIn("Cover every part of", sent_messages[0]["content"])
        self.assertIn("Never use outside knowledge", sent_messages[0]["content"])
        self.assertIn(json.dumps(profile), sent_messages[0]["content"])
        self.assertEqual(sent_messages[1:], messages)
        client.chat.assert_called_once_with(
            model="test-model",
            messages=sent_messages,
            think=False,
            stream=True,
            keep_alive=-1,
            options={
                "temperature": 0.3,
                "num_predict": 256,
                "num_ctx": 4096,
                "seed": 42,
                "top_p": 0.8,
                "top_k": 20,
            },
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
    def test_smalltalk_chat_rejects_chat_history(self, client_factory):
        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({
                "messages": [
                    {"role": "user", "content": "Earlier question"},
                    {"role": "assistant", "content": "Earlier answer"},
                    {"role": "user", "content": "Current question"},
                ],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Send only your current message; chat history is not accepted."},
        )
        client_factory.assert_not_called()

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_rejects_oversized_message(self, client_factory):
        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": "user", "content": "x" * 1001}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Each message must be 1000 characters or fewer."},
        )
        client_factory.assert_not_called()

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_rate_limits_ten_requests_per_minute(self, client_factory):
        client = client_factory.return_value
        client.chat.side_effect = lambda **kwargs: iter([{"message": {"content": "Hello back"}}])

        for _ in range(10):
            response = self.client.post(
                reverse("smalltalk_chat"),
                data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "60")
        self.assertEqual(
            response.json(),
            {"error": "Too many messages. Please wait a minute and try again."},
        )

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
            {"error": "The AI assistant is temporarily unavailable. Please try again later."},
        )

    @patch("portfolio.views.ollama.Client")
    def test_smalltalk_chat_reports_invalid_ollama_response(self, client_factory):
        client_factory.return_value.chat.return_value = iter([{"message": {}}])

        response = self.client.post(
            reverse("smalltalk_chat"),
            data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        stream_output = b"".join(response.streaming_content).decode()
        self.assertIn("event: error", stream_output)
        self.assertIn(
            "couldn't generate a reply".encode("utf-8").hex(),
            stream_output,
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
            {"error": "The AI assistant is temporarily unavailable. Please try again later."},
        )
