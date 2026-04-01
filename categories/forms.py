from django import forms
from django.utils import timezone
from expenses.forms import _merge_normalized_post_into_init_args
from .models import Category, CategoryBudget


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


class CategoryBudgetForm(forms.ModelForm):
    class Meta:
        model = CategoryBudget
        fields = ("category", "year", "month", "amount")

    def __init__(self, *args, user=None, **kwargs):
        args, kwargs = _merge_normalized_post_into_init_args(*args, field_names=("amount",), **kwargs)
        super().__init__(*args, **kwargs)
        self.user = user
        today = timezone.now().date()
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user).order_by("order", "name")
        self.fields["category"].widget.attrs.setdefault("class", "input-field")
        self.fields["year"].widget.attrs.setdefault("class", "input-field")
        self.fields["month"].widget.attrs.setdefault("class", "input-field")
        self.fields["amount"].widget = forms.TextInput(
            attrs={
                "class": "input-field",
                "placeholder": "Masalan: 500 000",
                "inputmode": "numeric",
                "autocomplete": "off",
            }
        )

        if not self.instance.pk:
            self.fields["year"].initial = today.year
            self.fields["month"].initial = today.month

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.pk:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
