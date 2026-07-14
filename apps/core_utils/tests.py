"""تست‌های واحد برای تبدیل تاریخ شمسی ↔ میلادی."""
import datetime

from django.test import TestCase

from apps.core_utils.fields import JalaliDateField
from apps.core_utils.jalali import jalali_to_gregorian, to_jalali_str


class JalaliConversionTests(TestCase):

    def test_jalali_to_gregorian_known_date(self):
        # اول فروردین ۱۴۰۳ برابر است با ۲۰ مارس ۲۰۲۴
        result = jalali_to_gregorian('1403/01/01')
        self.assertEqual(result, datetime.date(2024, 3, 20))

    def test_gregorian_to_jalali_string(self):
        result = to_jalali_str(datetime.date(2024, 3, 20))
        self.assertEqual(result, '1403/01/01')

    def test_invalid_jalali_string_returns_none(self):
        self.assertIsNone(jalali_to_gregorian('not-a-date'))

    def test_jalali_date_field_to_python(self):
        field = JalaliDateField()
        result = field.clean('1403/01/01')
        self.assertEqual(result, datetime.date(2024, 3, 20))

    def test_jalali_date_field_rejects_invalid_input(self):
        field = JalaliDateField()
        with self.assertRaises(Exception):
            field.clean('nonsense')
