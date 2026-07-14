from django import template

from apps.core_utils.jalali import to_jalali_str

register = template.Library()


@register.filter(name='jalali')
def jalali(value):
    """{{ some_date|jalali }} -> نمایش تاریخ به‌صورت شمسی (بدون ساعت)."""
    return to_jalali_str(value, with_time=False)


@register.filter(name='jalali_dt')
def jalali_dt(value):
    """{{ some_datetime|jalali_dt }} -> نمایش تاریخ و ساعت به‌صورت شمسی."""
    return to_jalali_str(value, with_time=True)
