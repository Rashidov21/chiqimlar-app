from django import forms
from django.utils import timezone
from .models import Expense, SavingGoal, RecurringExpense, Debt
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
        self.fields["amount"].widget.attrs["placeholder"] = "Summasi (so'm)"
        self.fields["amount"].widget.attrs["inputmode"] = "numeric"
        self.fields["amount"].widget.attrs["min"] = "0"
        self.fields["amount"].widget.attrs["step"] = "1000"
        self.fields["amount"].widget.attrs["autofocus"] = "autofocus"
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


class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ("name", "target_amount", "current_amount", "start_date", "target_date", "is_active")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not self.instance.pk:
            self.fields["start_date"].initial = timezone.now().date()

        for name in ("name", "target_amount", "current_amount", "start_date", "target_date"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("class", "input-field")

        self.fields["target_amount"].widget.attrs.setdefault("placeholder", "Maqsad summa (so'm)")
        self.fields["target_amount"].widget.attrs.setdefault("inputmode", "numeric")
        self.fields["current_amount"].widget.attrs.setdefault("placeholder", "Hozircha jamg'arilgan (ixtiyoriy)")
        self.fields["current_amount"].widget.attrs.setdefault("inputmode", "numeric")

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.pk:
            obj.user = self.user
        if commit:
            obj.save()
        return obj


class RecurringExpenseForm(forms.ModelForm):
    class Meta:
        model = RecurringExpense
        fields = ("name", "amount", "category", "interval", "next_payment_date", "is_active")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user).order_by("order", "name")
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Turkum (ixtiyoriy)"
        if not self.instance.pk:
            self.fields["next_payment_date"].initial = timezone.now().date()

        for name in ("name", "amount", "category", "interval", "next_payment_date"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("class", "input-field")

        self.fields["amount"].widget.attrs.setdefault("placeholder", "To'lov summasi (so'm)")
        self.fields["amount"].widget.attrs.setdefault("inputmode", "numeric")

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.pk:
            obj.user = self.user
        if commit:
            obj.save()
        return obj


class DebtForm(forms.ModelForm):
    class Meta:
        model = Debt
        fields = ("kind", "counterparty", "amount", "date", "due_date", "note", "is_closed")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not self.instance.pk:
            self.fields["date"].initial = timezone.now().date()

        for name in ("kind", "counterparty", "amount", "date", "due_date", "note"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("class", "input-field")

        self.fields["counterparty"].widget.attrs.setdefault("placeholder", "Ism yoki tashkilot nomi")
        self.fields["amount"].widget.attrs.setdefault("placeholder", "Qarz summasi (so'm)")
        self.fields["amount"].widget.attrs.setdefault("inputmode", "numeric")
        self.fields["note"].widget.attrs.setdefault("placeholder", "Izoh (ixtiyoriy)")

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.pk:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
