from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='نام کاربری',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control password-input'})
    )


class ProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل شخصی (بدون فیلدهای حساس مثل نقش یا دسترسی)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'bio', 'avatar']
        labels = {
            'first_name': 'نام', 'last_name': 'نام خانوادگی', 'email': 'ایمیل',
            'phone_number': 'شماره تماس', 'bio': 'توضیح کوتاه',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'avatar':
                field.widget.attrs.setdefault('class', 'form-control')
