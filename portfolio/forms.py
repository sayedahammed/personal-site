from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your name"}),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "placeholder": "you@example.com"}
            ),
            "subject": forms.TextInput(attrs={"placeholder": "What would you like to discuss?"}),
            "message": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Tell me a little about it..."}
            ),
        }
