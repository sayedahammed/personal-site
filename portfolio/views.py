from django.conf import settings
from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ContactForm


def home(request):
    return render(request, "home.html", {"contact_form": ContactForm()})


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
