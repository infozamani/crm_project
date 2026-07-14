from django import forms
from django.forms import inlineformset_factory

from apps.workshop.models import ServiceRequest, ServiceRequestMedia


class PortalServiceRequestForm(forms.ModelForm):
    """
    فرم ثبت درخواست تعمیر توسط خود مشتری از پرتال. فیلد مشتری در فرم وجود
    ندارد و در ویو، به‌صورت خودکار روی مشتری صاحب حساب تنظیم می‌شود.
    """

    class Meta:
        model = ServiceRequest
        fields = ['machine_identifier', 'fault_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control',
                                                    'placeholder': 'لطفاً مشکل دستگاه را با جزئیات شرح دهید...'}),
        }
        labels = {
            'machine_identifier': 'شناسه یا شماره شاسی دستگاه',
            'fault_type': 'نوع خرابی',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


# حداقل یک عکس یا فیلم برای ثبت درخواست الزامی است (extra=2 برای راحتی افزودن مورد دوم،
# min_num=1 + validate_min=True یعنی فرم بدون حداقل یک فایل معتبر نیست).
PortalServiceRequestMediaFormSet = inlineformset_factory(
    ServiceRequest, ServiceRequestMedia,
    fields=['file'],
    extra=2, min_num=1, validate_min=True, can_delete=True,
    widgets={'file': forms.ClearableFileInput(attrs={'class': 'form-control'})}
)


class ServiceRequestRatingForm(forms.ModelForm):
    """فرم ثبت رضایت‌سنجی (۱ تا ۵ ستاره) پس از تحویل دستگاه."""

    class Meta:
        model = ServiceRequest
        fields = ['customer_rating', 'customer_feedback']
        widgets = {
            'customer_rating': forms.RadioSelect(),
            'customer_feedback': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': 'نظر شما درباره کیفیت تعمیر و برخورد تیم ما (اختیاری)'
            }),
        }
        labels = {'customer_rating': 'میزان رضایت شما از این تعمیر', 'customer_feedback': 'توضیحات (اختیاری)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer_rating'].required = True
