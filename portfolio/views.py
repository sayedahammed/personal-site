import json
import logging

import httpx
import ollama
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ContactForm


logger = logging.getLogger(__name__)
SMALLTALK_MAX_MESSAGES = 12
SMALLTALK_MAX_MESSAGE_LENGTH = 1000


def home(request):
    return render(request, "home.html", {"contact_form": ContactForm()})


@require_POST
def smalltalk_chat(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Send a valid chat request."}, status=400)

    messages = payload.get("messages") if isinstance(payload, dict) else None
    if not isinstance(messages, list) or not 1 <= len(messages) <= SMALLTALK_MAX_MESSAGES:
        return JsonResponse({"error": "Send between 1 and 12 messages."}, status=400)

    validated_messages = []
    for message in messages:
        if not isinstance(message, dict):
            return JsonResponse({"error": "Each message must include a role and content."}, status=400)
        role = message.get("role")
        content = message.get("content")
        if (
            not isinstance(role, str)
            or role not in {"user", "assistant"}
            or not isinstance(content, str)
            or not content.strip()
            or len(content) > SMALLTALK_MAX_MESSAGE_LENGTH
        ):
            return JsonResponse({"error": "A message is empty or invalid."}, status=400)
        validated_messages.append({"role": role, "content": content.strip()})

    if validated_messages[-1]["role"] != "user":
        return JsonResponse({"error": "The last message must be from you."}, status=400)

    try:
        client = ollama.Client(host=settings.OLLAMA_HOST)
        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=validated_messages,
            think=False,
            stream=False,
            keep_alive=-1,
            options={
                "num_predict": 64,
                "num_thread": 4,
            },
        )
    except ollama.ResponseError:
        logger.exception("Ollama returned an error while handling a SmallTalk request.")
        return JsonResponse(
            {"error": "Qwen3 Chat couldn't generate a reply. Please try again."},
            status=502,
        )
    except httpx.HTTPError:
        logger.exception("Ollama is unavailable while handling a SmallTalk request.")
        return JsonResponse(
            {"error": "Qwen3 Chat is temporarily unavailable. Please try again later."},
            status=503,
        )
    except Exception:
        logger.exception("Unexpected Ollama client failure while handling a SmallTalk request.")
        return JsonResponse(
            {"error": "Qwen3 Chat is temporarily unavailable. Please try again later."},
            status=503,
        )

    message = response.get("message") if isinstance(response, dict) else getattr(response, "message", None)
    reply = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
    if not isinstance(reply, str) or not reply.strip():
        logger.error("Ollama returned an invalid SmallTalk response.")
        return JsonResponse(
            {"error": "Qwen3 Chat couldn't generate a reply. Please try again."},
            status=502,
        )

    return JsonResponse({"reply": reply.strip()})


def contact(request):
    if request.method != "POST":
        return redirect(f"{reverse('home')}#contact")

    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thanks for reaching out. Your message has been received.")
        return redirect(f"{reverse('home')}#contact")

    return render(request, "home.html", {"contact_form": form}, status=400)


def download_resume(request):
    resume_path = settings.BASE_DIR / "MD_SAYED_AHAMMED_RESUME.pdf"
    return FileResponse(
        resume_path.open("rb"),
        as_attachment=True,
        filename="Sayed-Ahammed-Resume.pdf",
        content_type="application/pdf",
    )
