from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.customers.models import Customer, SalesOpportunity


def generate_quote_number():
    """تولید شماره سریال خودکار پیش‌فاکتور بر اساس آخرین رکورد."""
    last = Quote.objects.order_by('id').last()
    next_id = (last.id + 1) if last else 1
    return f'Q-{timezone.now().year}-{next_id:05d}'


class Quote(models.Model):
    """پیش‌فاکتور مرتبط با یک فرصت فروش."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس (هنوز ارسال نشده)'
        SENT = 'sent', 'ارسال‌شده برای مشتری (در انتظار تایید)'
        APPROVED = 'approved', 'تایید شده توسط مشتری'
        REJECTED = 'rejected', 'رد شده توسط مشتری'

    number = models.CharField(max_length=32, unique=True, editable=False, verbose_name='شماره پیش‌فاکتور')
    opportunity = models.ForeignKey(SalesOpportunity, on_delete=models.CASCADE, related_name='quotes',
                                     verbose_name='فرصت فروش')
    valid_until = models.DateField(verbose_name='تاریخ اعتبار')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'),
                                            verbose_name='درصد تخفیف')
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9'),
                                       verbose_name='درصد مالیات')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, verbose_name='وضعیت')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ارسال به مشتری')
    customer_responded_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پاسخ مشتری')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    verbose_name='ایجادکننده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'پیش‌فاکتور'
        verbose_name_plural = 'پیش‌فاکتورها'
        ordering = ['-created_at']

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = generate_quote_number()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('sales:quote_detail', args=[self.pk])

    def get_portal_absolute_url(self):
        return reverse('portal:quote_detail', args=[self.pk])

    @property
    def subtotal(self) -> Decimal:
        return sum((item.line_total for item in self.items.all()), Decimal('0'))

    @property
    def discount_amount(self) -> Decimal:
        return self.subtotal * self.discount_percent / Decimal('100')

    @property
    def taxable_amount(self) -> Decimal:
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self) -> Decimal:
        return self.taxable_amount * self.tax_percent / Decimal('100')

    @property
    def total_amount(self) -> Decimal:
        return self.taxable_amount + self.tax_amount

    @property
    def is_expired(self) -> bool:
        return self.valid_until < timezone.now().date()


class QuoteItem(models.Model):
    """آیتم‌های پیش‌فاکتور."""

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items', verbose_name='پیش‌فاکتور')
    description = models.CharField(max_length=255, verbose_name='شرح')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1'), verbose_name='تعداد')
    unit_price = models.DecimalField(max_digits=16, decimal_places=0, verbose_name='قیمت واحد (ریال)')

    class Meta:
        verbose_name = 'آیتم پیش‌فاکتور'
        verbose_name_plural = 'آیتم‌های پیش‌فاکتور'

    def __str__(self):
        return f'{self.description} x {self.quantity}'

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


class Contract(models.Model):
    """قرارداد فروش نهایی."""

    class ContractType(models.TextChoices):
        CASH = 'cash', 'نقدی'
        INSTALLMENT = 'installment', 'اقساطی'
        LEASING = 'leasing', 'لیزینگ'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'فعال'
        COMPLETED = 'completed', 'تکمیل‌شده'
        CANCELLED = 'cancelled', 'لغو‌شده'

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='contracts', verbose_name='مشتری')
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='contracts', verbose_name='پیش‌فاکتور مرجع')
    contract_type = models.CharField(max_length=16, choices=ContractType.choices, verbose_name='نوع قرارداد')
    signed_date = models.DateField(verbose_name='تاریخ امضا')
    total_amount = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='مبلغ کل (ریال)')
    down_payment = models.DecimalField(max_digits=18, decimal_places=0, default=Decimal('0'),
                                        verbose_name='مبلغ پیش‌پرداخت')
    installments_count = models.PositiveIntegerField(default=0, verbose_name='تعداد اقساط')
    installment_amount = models.DecimalField(max_digits=18, decimal_places=0, default=Decimal('0'),
                                              verbose_name='مبلغ هر قسط')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, verbose_name='وضعیت')
    attachment = models.FileField(upload_to='contracts/%Y/%m/', blank=True, null=True,
                                   verbose_name='فایل پیوست قرارداد')
    is_confirmed_by_customer = models.BooleanField(
        default=False, verbose_name='تایید شده توسط مشتری',
        help_text='وقتی مشتری از پرتال خودش این قرارداد را تایید کند، این فیلد True می‌شود.'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تایید مشتری')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    verbose_name='ثبت‌کننده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')

    class Meta:
        verbose_name = 'قرارداد'
        verbose_name_plural = 'قراردادها'
        ordering = ['-signed_date']

    def __str__(self):
        return f'قرارداد {self.pk} - {self.customer}'

    def get_absolute_url(self):
        return reverse('sales:contract_detail', args=[self.pk])

    @property
    def remaining_amount(self) -> Decimal:
        return self.total_amount - self.down_payment

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.contract_type in (self.ContractType.INSTALLMENT, self.ContractType.LEASING):
            if self.installments_count <= 0:
                raise ValidationError('برای قراردادهای اقساطی/لیزینگ باید تعداد اقساط مشخص شود.')
            expected_installment = self.remaining_amount / self.installments_count
            # اجازه اختلاف گرد شدن تا ۱۰۰۰ ریال
            if abs(expected_installment - self.installment_amount) > 1000 and self.installment_amount:
                raise ValidationError('مبلغ هر قسط با محاسبه (مبلغ باقی‌مانده / تعداد اقساط) همخوانی ندارد.')


class Check(models.Model):
    """چک‌های دریافتی مرتبط با یک قرارداد."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'وصول‌نشده'
        CLEARED = 'cleared', 'وصول‌شده'
        BOUNCED = 'bounced', 'برگشتی'

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='checks', verbose_name='قرارداد')
    check_number = models.CharField(max_length=64, verbose_name='شماره چک')
    due_date = models.DateField(verbose_name='تاریخ سررسید')
    amount = models.DecimalField(max_digits=18, decimal_places=0, verbose_name='مبلغ')
    issuing_bank = models.CharField(max_length=128, verbose_name='بانک صادرکننده')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, verbose_name='وضعیت')

    class Meta:
        verbose_name = 'چک'
        verbose_name_plural = 'چک‌ها'
        ordering = ['due_date']
        unique_together = ('contract', 'check_number')

    def __str__(self):
        return f'چک {self.check_number} - {self.amount}'


class DeliverySchedule(models.Model):
    """مراحل تحویل دستگاه مرتبط با یک قرارداد."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='delivery_schedules',
                                  verbose_name='قرارداد')
    scheduled_date = models.DateField(verbose_name='تاریخ برنامه‌ریزی‌شده')
    description = models.CharField(max_length=255, verbose_name='شرح مرحله')
    is_completed = models.BooleanField(default=False, verbose_name='تکمیل‌شده')

    class Meta:
        verbose_name = 'مرحله تحویل'
        verbose_name_plural = 'مراحل تحویل'
        ordering = ['scheduled_date']

    def __str__(self):
        return f'{self.description} - {self.contract}'
