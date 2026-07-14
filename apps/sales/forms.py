from django import forms
from django.forms import inlineformset_factory

from apps.core_utils.fields import JalaliDateField

from .models import Quote, QuoteItem, Contract, Check, DeliverySchedule


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif not isinstance(field.widget, forms.TextInput) or 'class' not in field.widget.attrs:
                field.widget.attrs.setdefault('class', 'form-control')


class QuoteForm(BootstrapFormMixin, forms.ModelForm):
    valid_until = JalaliDateField(label='تاریخ اعتبار')

    class Meta:
        model = Quote
        fields = ['opportunity', 'valid_until', 'discount_percent', 'tax_percent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


QuoteItemFormSet = inlineformset_factory(
    Quote, QuoteItem,
    fields=['description', 'quantity', 'unit_price'],
    extra=1, can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)


class ContractForm(BootstrapFormMixin, forms.ModelForm):
    signed_date = JalaliDateField(label='تاریخ امضا')

    class Meta:
        model = Contract
        fields = ['customer', 'quote', 'contract_type', 'signed_date', 'total_amount',
                   'down_payment', 'installments_count', 'installment_amount', 'status', 'attachment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


CheckFormSet = inlineformset_factory(
    Contract, Check,
    fields=['check_number', 'due_date', 'amount', 'issuing_bank', 'status'],
    field_classes={'due_date': JalaliDateField},
    extra=1, can_delete=True,
    widgets={
        'check_number': forms.TextInput(attrs={'class': 'form-control'}),
        'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        'issuing_bank': forms.TextInput(attrs={'class': 'form-control'}),
        'status': forms.Select(attrs={'class': 'form-control'}),
    }
)

DeliveryScheduleFormSet = inlineformset_factory(
    Contract, DeliverySchedule,
    fields=['scheduled_date', 'description', 'is_completed'],
    field_classes={'scheduled_date': JalaliDateField},
    extra=1, can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control'}),
        'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)
