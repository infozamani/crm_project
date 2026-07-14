from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse


national_id_validator = RegexValidator(
    regex=r'^\d{10,11}$',
    message='کد ملی/اقتصادی باید بین ۱۰ تا ۱۱ رقم باشد.'
)


class Customer(models.Model):
    """مشتری، اعم از حقیقی یا حقوقی."""

    class CustomerType(models.TextChoices):
        INDIVIDUAL = 'individual', 'حقیقی'
        LEGAL = 'legal', 'حقوقی'

    customer_type = models.CharField(max_length=16, choices=CustomerType.choices,
                                      default=CustomerType.LEGAL, verbose_name='نوع مشتری')
    name = models.CharField(max_length=255, verbose_name='نام / نام شرکت')
    national_or_economic_id = models.CharField(
        max_length=11, unique=True, validators=[national_id_validator],
        verbose_name='کد ملی / کد اقتصادی'
    )
    phone_number = models.CharField(max_length=20, verbose_name='تلفن')
    secondary_phone = models.CharField(max_length=20, blank=True, verbose_name='تلفن دوم')
    address = models.TextField(blank=True, verbose_name='آدرس')
    is_verified = models.BooleanField(default=False, verbose_name='اعتبارسنجی شده')
    assigned_sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='customers', verbose_name='کارشناس فروش مسئول'
    )
    portal_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='customer_record', verbose_name='حساب کاربری پرتال مشتری',
        help_text='در صورت ایجاد، این مشتری می‌تواند با این حساب وارد پرتال مشتری شود.'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')

    class Meta:
        verbose_name = 'مشتری'
        verbose_name_plural = 'مشتریان'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('customers:customer_detail', args=[self.pk])


class SalesOpportunity(models.Model):
    """فرصت فروش مرتبط با یک مشتری."""

    class Status(models.TextChoices):
        SERIOUS = 'serious', 'جدی'
        NEGOTIATION = 'negotiation', 'در حال مذاکره'
        QUOTE_SENT = 'quote_sent', 'ارسال پیش‌فاکتور'
        CLOSED_WON = 'closed_won', 'بسته‌شده (موفق)'
        CANCELLED = 'cancelled', 'لغو‌شده'

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='opportunities',
                                  verbose_name='مشتری')
    title = models.CharField(max_length=255, verbose_name='عنوان پروژه')
    machine_model = models.CharField(max_length=255, verbose_name='مدل دستگاه')
    estimated_budget = models.DecimalField(max_digits=16, decimal_places=0, verbose_name='بودجه تقریبی (ریال)')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SERIOUS, verbose_name='وضعیت')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='opportunities', verbose_name='کارشناس مسئول')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')

    class Meta:
        verbose_name = 'فرصت فروش'
        verbose_name_plural = 'فرصت‌های فروش'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.customer}'

    def get_absolute_url(self):
        return reverse('customers:opportunity_detail', args=[self.pk])


class Interaction(models.Model):
    """ثبت تعاملات (تماس، جلسه، پیگیری) با مشتری."""

    class InteractionType(models.TextChoices):
        CALL = 'call', 'تماس تلفنی'
        MEETING = 'meeting', 'جلسه حضوری'
        FOLLOW_UP = 'follow_up', 'پیگیری'
        EMAIL = 'email', 'ایمیل'

    opportunity = models.ForeignKey(SalesOpportunity, on_delete=models.CASCADE, related_name='interactions',
                                     verbose_name='فرصت فروش')
    interaction_type = models.CharField(max_length=16, choices=InteractionType.choices, verbose_name='نوع تعامل')
    date = models.DateTimeField(verbose_name='تاریخ')
    notes = models.TextField(blank=True, verbose_name='توضیحات')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    verbose_name='ثبت‌کننده')

    class Meta:
        verbose_name = 'تعامل'
        verbose_name_plural = 'تعاملات'
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_interaction_type_display()} - {self.opportunity}'
