"""تست‌های واحد برای مدل‌های ماژول فروش و قراردادها."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.customers.models import Customer, SalesOpportunity
from apps.sales.models import Quote, QuoteItem, Contract

User = get_user_model()


class QuoteCalculationTests(TestCase):
    """تست محاسبه مبلغ نهایی پیش‌فاکتور (جمع جزء، تخفیف، مالیات)."""

    def setUp(self):
        self.customer = Customer.objects.create(
            name='مشتری تست', national_or_economic_id='1234567890', phone_number='09120000000'
        )
        self.opportunity = SalesOpportunity.objects.create(
            customer=self.customer, title='فرصت تست', machine_model='CAT 320',
            estimated_budget=1000000000, status=SalesOpportunity.Status.SERIOUS,
        )
        self.quote = Quote.objects.create(
            opportunity=self.opportunity, valid_until=timezone.now().date() + timedelta(days=10),
            discount_percent=Decimal('10'), tax_percent=Decimal('9'),
        )
        QuoteItem.objects.create(quote=self.quote, description='دستگاه', quantity=1, unit_price=Decimal('1000000000'))
        QuoteItem.objects.create(quote=self.quote, description='حمل و نصب', quantity=1, unit_price=Decimal('50000000'))

    def test_subtotal_calculation(self):
        self.assertEqual(self.quote.subtotal, Decimal('1050000000'))

    def test_total_amount_with_discount_and_tax(self):
        # جمع جزء ۱,۰۵۰,۰۰۰,۰۰۰ - تخفیف ۱۰٪ = ۹۴۵,۰۰۰,۰۰۰ + مالیات ۹٪ = ۱,۰۳۰,۰۵۰,۰۰۰
        expected_total = Decimal('1030050000.00')
        self.assertEqual(self.quote.total_amount, expected_total)

    def test_quote_number_auto_generated(self):
        self.assertTrue(self.quote.number.startswith(f'Q-{timezone.now().year}-'))

    def test_quote_is_expired_property(self):
        expired_quote = Quote.objects.create(
            opportunity=self.opportunity, valid_until=timezone.now().date() - timedelta(days=1),
        )
        self.assertTrue(expired_quote.is_expired)
        self.assertFalse(self.quote.is_expired)


class ContractValidationTests(TestCase):
    """تست اعتبارسنجی محاسبه مبلغ اقساط قرارداد."""

    def setUp(self):
        self.customer = Customer.objects.create(
            name='مشتری قرارداد', national_or_economic_id='9876543210', phone_number='09121111111'
        )

    def test_installment_amount_must_match_calculation(self):
        contract = Contract(
            customer=self.customer, contract_type=Contract.ContractType.INSTALLMENT,
            signed_date=timezone.now().date(), total_amount=Decimal('1000000000'),
            down_payment=Decimal('200000000'), installments_count=8,
            installment_amount=Decimal('999999'),  # مقدار عمداً نادرست
        )
        with self.assertRaises(ValidationError):
            contract.clean()

    def test_valid_installment_amount_passes_clean(self):
        remaining = Decimal('800000000')
        contract = Contract(
            customer=self.customer, contract_type=Contract.ContractType.INSTALLMENT,
            signed_date=timezone.now().date(), total_amount=Decimal('1000000000'),
            down_payment=Decimal('200000000'), installments_count=8,
            installment_amount=remaining / 8,
        )
        try:
            contract.clean()
        except ValidationError:
            self.fail('clean() نباید برای مبلغ صحیح اقساط خطا بدهد.')

    def test_remaining_amount_property(self):
        contract = Contract.objects.create(
            customer=self.customer, contract_type=Contract.ContractType.CASH,
            signed_date=timezone.now().date(), total_amount=Decimal('500000000'),
            down_payment=Decimal('100000000'),
        )
        self.assertEqual(contract.remaining_amount, Decimal('400000000'))
