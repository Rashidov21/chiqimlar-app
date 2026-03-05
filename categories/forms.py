from django import forms
from .models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "emoji", "order")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["name"].widget.attrs["class"] = "input-field"
        self.fields["name"].widget.attrs["placeholder"] = "Turkum nomi"
        self.fields["emoji"].widget.attrs["class"] = "input-field"
        self.fields["emoji"].widget.attrs["placeholder"] = "😊 (masalan, 🍔)"
        self.fields["emoji"].widget.attrs["maxlength"] = "3"
        self.fields["order"].widget.attrs["class"] = "input-field"

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
