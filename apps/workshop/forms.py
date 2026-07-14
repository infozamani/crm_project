from django import forms
from django.forms import inlineformset_factory

from apps.core_utils.fields import JalaliDateField

from .models import ServiceRequest, ServiceRequestImage, Technician, TaskAssignment, RepairLog, FieldService, CostEstimate


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class ServiceRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['customer', 'machine_identifier', 'fault_type', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


ServiceRequestImageFormSet = inlineformset_factory(
    ServiceRequest, ServiceRequestImage,
    fields=['image'],
    extra=1, can_delete=True,
    widgets={'image': forms.ClearableFileInput(attrs={'class': 'form-control'})}
)


class TechnicianForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Technician
        fields = ['user', 'specialty', 'rank']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class TaskAssignmentForm(BootstrapFormMixin, forms.ModelForm):
    start_date = JalaliDateField(label='تاریخ شروع')
    end_date = JalaliDateField(label='تاریخ پایان', required=False)

    class Meta:
        model = TaskAssignment
        fields = ['technician', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class RepairLogForm(BootstrapFormMixin, forms.ModelForm):
    date = JalaliDateField(label='تاریخ')

    class Meta:
        model = RepairLog
        fields = ['date', 'parts_used', 'hours_spent', 'notes']
        widgets = {
            'parts_used': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class FieldServiceForm(BootstrapFormMixin, forms.ModelForm):
    date = JalaliDateField(label='تاریخ')

    class Meta:
        model = FieldService
        fields = ['service_request', 'technician', 'address', 'date', 'status']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CostEstimateForm(BootstrapFormMixin, forms.ModelForm):
    """فرم ثبت برآورد قیمت توسط تکنسین، برای ارسال به مدیر فروش جهت تایید."""

    class Meta:
        model = CostEstimate
        fields = ['estimated_cost', 'estimated_hours', 'parts_needed', 'notes']
        widgets = {
            'parts_needed': forms.Textarea(attrs={'rows': 2, 'placeholder': 'مثلاً: ۲ عدد واشر هیدرولیک'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'estimated_cost': 'برآورد هزینه (ریال)',
            'estimated_hours': 'برآورد ساعت کار',
            'parts_needed': 'قطعات مورد نیاز (برآوردی)',
            'notes': 'توضیحات فنی',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
