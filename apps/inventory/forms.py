from django import forms

from apps.core_utils.fields import JalaliDateField

from .models import Part, InventoryTransaction, PartRequest


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


class PartForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Part
        fields = ['name', 'code', 'brand', 'min_stock', 'max_stock', 'unit_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class InventoryTransactionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['part', 'transaction_type', 'quantity', 'reference_repair_order', 'purchase_order_reference']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class TurnoverReportFilterForm(forms.Form):
    date_from = JalaliDateField(required=False, label='از تاریخ')
    date_to = JalaliDateField(required=False, label='تا تاریخ')
    part = forms.ModelChoiceField(queryset=Part.objects.all(), required=False,
                                    widget=forms.Select(attrs={'class': 'form-select'}))


class PartRequestForm(BootstrapFormMixin, forms.ModelForm):
    """فرم درخواست قطعه توسط تکنسین از انبار."""

    class Meta:
        model = PartRequest
        fields = ['part', 'quantity_requested', 'note']
        labels = {'quantity_requested': 'تعداد مورد نیاز', 'note': 'توضیح (اختیاری)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
