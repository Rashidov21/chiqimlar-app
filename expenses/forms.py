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
        self.fields["amount"].widget.attrs["placeholder"] = "Masalan: 1 000 000"
        self.fields["amount"].widget.attrs["inputmode"] = "numeric"
        self.fields["amount"].widget.attrs["min"] = "0"
        self.fields["amount"].widget.attrs["step"] = "1000"
        self.fields["amount"].widget.attrs["autofocus"] = "autofocus"
        self.fields["note"].widget.attrs["class"] = "input-field"
        self.fields["note"].widget.attrs["placeholder"] = "Izoh (to'ldirish shart emas)"
        self.fields["note"].widget.attrs["maxlength"] = "255"
        self.fields["date"].widget.attrs["class"] = "input-field"
        self.fields["category"].widget.attrs["class"] = "input-field"

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None:
            return amount
        if amount <= 0:
            raise forms.ValidationError("Summani musbat qiymat sifatida kiriting.")
        return amount

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

        self.fields["target_amount"].widget.attrs.setdefault("placeholder", "Masalan: 5 000 000")
        self.fields["target_amount"].widget.attrs.setdefault("inputmode", "numeric")
        self.fields["current_amount"].widget.attrs.setdefault("placeholder", "0 yoki masalan: 1 000 000")
        self.fields["current_amount"].widget.attrs.setdefault("inputmode", "numeric")

    def clean_target_amount(self):
        value = self.cleaned_data.get("target_amount")
        if value is None:
            return value
        if value <= 0:
            raise forms.ValidationError("Maqsad summasi 0 dan katta bo'lishi kerak.")
        return value

    def clean_current_amount(self):
        current = self.cleaned_data.get("current_amount") or 0
        target = self.cleaned_data.get("target_amount") or 0
        if current < 0:
            raise forms.ValidationError("Jamg'arilgan summa manfiy bo'lmasligi kerak.")
        if target and current > target:
            raise forms.ValidationError("Jamg'arilgan summa maqsad summasidan oshmasligi kerak.")
        return current

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

        self.fields["amount"].widget.attrs.setdefault("placeholder", "Masalan: 500 000")
        self.fields["amount"].widget.attrs.setdefault("inputmode", "numeric")

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None:
            return amount
        if amount <= 0:
            raise forms.ValidationError("To'lov summasi 0 dan katta bo'lishi kerak.")
        return amount

    def clean_next_payment_date(self):
        value = self.cleaned_data.get("next_payment_date")
        if value is None:
            return value
        today = timezone.now().date()
        # Juda eski sana bo'lsa foydalanuvchini ogohlantirish: kamida bugundan 1 oy ichida bo'lsin
        if value < today.replace(year=today.year - 1):
            raise forms.ValidationError("Keyingi to'lov sanasi juda eski. Yaqinroq sanani tanlang.")
        return value

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
        self.fields["amount"].widget.attrs.setdefault("placeholder", "Masalan: 1 000 000")
        self.fields["amount"].widget.attrs.setdefault("inputmode", "numeric")
        self.fields["note"].widget.attrs.setdefault("placeholder", "Izoh (ixtiyoriy)")

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None:
            return amount
        if amount <= 0:
            raise forms.ValidationError("Qarz summasi 0 dan katta bo'lishi kerak.")
        return amount

    def clean_due_date(self):
        due = self.cleaned_data.get("due_date")
        date = self.cleaned_data.get("date")
        if due and date and due < date:
            raise forms.ValidationError("Qaytarish muddati qarz sanasidan oldin bo'lishi mumkin emas.")
        return due

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.pk:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
