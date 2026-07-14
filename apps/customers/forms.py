from django import forms

from apps.core_utils.fields import JalaliDateTimeField

from .models import Customer, SalesOpportunity, Interaction


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_type', 'name', 'national_or_economic_id', 'phone_number',
                  'secondary_phone', 'address', 'is_verified', 'assigned_sales_rep']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class SalesOpportunityForm(forms.ModelForm):
    class Meta:
        model = SalesOpportunity
        fields = ['customer', 'title', 'machine_model', 'estimated_budget', 'status', 'owner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class InteractionForm(forms.ModelForm):
    date = JalaliDateTimeField(label='تاریخ و ساعت')

    class Meta:
        model = Interaction
        fields = ['interaction_type', 'date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['interaction_type'].widget.attrs.setdefault('class', 'form-control')
