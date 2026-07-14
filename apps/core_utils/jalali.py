"""
توابع کمکی تبدیل تاریخ میلادی ↔ شمسی.
تاریخ‌ها همیشه در دیتابیس به‌صورت میلادی (استاندارد) ذخیره می‌شوند؛ این ماژول
فقط برای «نمایش» و «دریافت ورودی» شمسی از کاربر استفاده می‌شود.
"""
import datetime

import jdatetime

WEEKDAY_NAMES_FA = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']


def to_jalali_str(value, with_time=False):
    """تبدیل date/datetime میلادی به رشته شمسی (مثلاً ۱۴۰۳/۰۴/۱۵)."""
    if value is None or value == '':
        return ''
    if isinstance(value, datetime.datetime):
        jd = jdatetime.datetime.fromgregorian(datetime=value)
        base = jd.strftime('%Y/%m/%d')
        return f'{base} - {jd.strftime("%H:%M")}' if with_time else base
    if isinstance(value, datetime.date):
        jd = jdatetime.date.fromgregorian(date=value)
        return jd.strftime('%Y/%m/%d')
    return str(value)


def jalali_to_gregorian(jalali_str):
    """
    تبدیل رشته تاریخ شمسی (فرمت YYYY/MM/DD یا YYYY-MM-DD) به شیء date میلادی.
    در صورت نامعتبر بودن ورودی، None برمی‌گرداند.
    """
    if not jalali_str:
        return None
    normalized = jalali_str.strip().replace('-', '/')
    try:
        year, month, day = [int(p) for p in normalized.split('/')]
        return jdatetime.date(year, month, day).togregorian()
    except (ValueError, TypeError):
        return None
