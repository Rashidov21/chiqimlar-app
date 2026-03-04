from django import forms
from django.utils import timezone
from .models import Expense
from categories.models import Category


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ("category", "amount", "note", "date")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user).order_by("order", "name")
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Chiqim turkumi"
        self.fields["date"].initial = timezone.now().date()
        self.fields["amount"].widget.attrs["class"] = "input-field"
        self.fields["amount"].widget.attrs["placeholder"] = "Summasi"
        self.fields["amount"].widget.attrs["inputmode"] = "numeric"
        self.fields["note"].widget.attrs["class"] = "input-field"
        self.fields["note"].widget.attrs["placeholder"] = "Izoh (to'ldirish shart emas)"
        self.fields["note"].widget.attrs["maxlength"] = "255"
        self.fields["date"].widget.attrs["class"] = "input-field"
        self.fields["category"].widget.attrs["class"] = "input-field"

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
