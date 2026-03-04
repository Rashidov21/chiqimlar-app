from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class LoginForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        label="Tasdiqlash kodi",
        error_messages={"min_length": "Kod 6 ta belgidan iborat bo‘lishi kerak.", "max_length": "Kod 6 ta belgidan iborat bo‘lishi kerak."},
        widget=forms.TextInput(
            attrs={
                "placeholder": "000000",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": "[0-9A-Za-z]*",
                "maxlength": "6",
                "class": "input-field",
            }
        ),
    )


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "input-field"
        self.fields["username"].widget.attrs["placeholder"] = "Login"
        self.fields["first_name"].widget.attrs["class"] = "input-field"
        self.fields["first_name"].widget.attrs["placeholder"] = "Ism"
        self.fields["password1"].widget.attrs["class"] = "input-field"
        self.fields["password1"].help_text = "Kamida 8 belgi (harf va raqam aralashmasi yaxshiroq)."
        self.fields["password2"].widget.attrs["class"] = "input-field"
        self.fields["password2"].widget.attrs["placeholder"] = "Parolni takrorlang"
