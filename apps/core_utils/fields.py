"""فیلدهای فرم سفارشی برای دریافت تاریخ شمسی و ذخیره آن به‌صورت میلادی در مدل."""
from django import forms
from django.core.exceptions import ValidationError

from .jalali import jalali_to_gregorian, to_jalali_str


class JalaliDateWidget(forms.TextInput):
    """
    ورودی متنی ساده برای تاریخ شمسی. با کلاس CSS مشخص، یک تقویم شمسی سبک
    (persian-datepicker، بارگذاری‌شده از CDN در base.html) به این ورودی متصل
    می‌شود؛ اما حتی بدون جاوااسکریپت هم کاربر می‌تواند تاریخ را با فرمت
    ۱۴۰۳/۰۴/۱۵ به‌صورت دستی تایپ کند، چون اعتبارسنجی در سمت سرور انجام می‌شود.
    """

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control jalali-date-input',
            'placeholder': 'مثال: 1403/04/15',
            'dir': 'ltr',
            'autocomplete': 'off',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class JalaliDateField(forms.CharField):
    """
    فیلد فرم که مقدار نمایش‌داده‌شده و دریافت‌شده از کاربر را به‌صورت شمسی
    نگه می‌دارد، اما هنگام clean() آن را به یک شیء date میلادی (سازگار با
    مدل Django) تبدیل می‌کند.
    """
    widget = JalaliDateWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('help_text', 'فرمت: سال/ماه/روز شمسی، مثلاً 1403/04/15')
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return None
        parsed = jalali_to_gregorian(value)
        if parsed is None:
            raise ValidationError('فرمت تاریخ نامعتبر است. لطفاً به‌صورت 1403/04/15 وارد کنید.')
        return parsed

    def prepare_value(self, value):
        # value ممکن است یک شیء date میلادی (از instance مدل) یا رشته (از POST) باشد
        import datetime
        if isinstance(value, (datetime.date, datetime.datetime)):
            return to_jalali_str(value)
        return value


class JalaliDateTimeWidget(forms.TextInput):
    """ورودی متنی برای تاریخ و ساعت شمسی، فرمت: 1403/04/15 14:30"""

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control jalali-datetime-input',
            'placeholder': 'مثال: 1403/04/15 14:30',
            'dir': 'ltr',
            'autocomplete': 'off',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class JalaliDateTimeField(forms.CharField):
    """نسخه تاریخ+ساعت JalaliDateField؛ برای فیلدهایی مثل زمان دقیق یک تعامل."""
    widget = JalaliDateTimeWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('help_text', 'فرمت: 1403/04/15 14:30')
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        import datetime
        from django.utils import timezone as dj_timezone
        if not value:
            return None
        value = value.strip()
        try:
            if ' ' in value:
                date_part, time_part = value.split(' ', 1)
            else:
                date_part, time_part = value, '00:00'
            greg_date = jalali_to_gregorian(date_part)
            if greg_date is None:
                raise ValueError
            hour, minute = [int(p) for p in time_part.split(':')]
            naive = datetime.datetime.combine(greg_date, datetime.time(hour=hour, minute=minute))
            return dj_timezone.make_aware(naive) if dj_timezone.is_naive(naive) else naive
        except (ValueError, TypeError):
            raise ValidationError('فرمت تاریخ/ساعت نامعتبر است. مثال درست: 1403/04/15 14:30')

    def prepare_value(self, value):
        import datetime
        if isinstance(value, (datetime.date, datetime.datetime)):
            return to_jalali_str(value, with_time=True)
        return value
