from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

from apps.customers.models import Customer


class Technician(models.Model):
    """تکنسین تعمیرگاه."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='technician_profile',
                                 verbose_name='حساب کاربری')
    specialty = models.CharField(max_length=255, verbose_name='تخصص')
    rank = models.CharField(max_length=64, blank=True, verbose_name='رتبه')

    class Meta:
        verbose_name = 'تکنسین'
        verbose_name_plural = 'تکنسین‌ها'

    def __str__(self):
        return f'{self.user} ({self.specialty})'


def service_request_upload_path(instance, filename):
    return f'service_requests/{instance.service_request_id}/{filename}'


class ServiceRequest(models.Model):
    """درخواست پذیرش دستگاه برای تعمیر."""

    class Status(models.TextChoices):
        PENDING_REVIEW = 'pending_review', 'در انتظار بررسی'
        IN_REPAIR = 'in_repair', 'در حال تعمیر'
        COMPLETED = 'completed', 'تکمیل‌شده'
        DELIVERED = 'delivered', 'تحویل داده‌شده'

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='service_requests',
                                  verbose_name='مشتری')
    machine_identifier = models.CharField(max_length=255, verbose_name='شناسه/شاسی دستگاه')
    received_at = models.DateField(auto_now_add=True, verbose_name='تاریخ پذیرش')
    fault_type = models.CharField(max_length=255, verbose_name='نوع خرابی')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING_REVIEW,
                               verbose_name='وضعیت')

    # رضایت‌سنجی مشتری: پس از تحویل دستگاه، مشتری از پرتال خودش امتیاز ۱ تا ۵
    # ستاره ثبت می‌کند. تا وقتی ثبت نشده، در پرتال مشتری به‌صورت برجسته
    # یادآوری می‌شود (نه یک قفل سخت‌گیرانه که مانع کار دیگری شود).
    customer_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=[(i, f'{i} ستاره') for i in range(1, 6)],
        verbose_name='امتیاز رضایت مشتری'
    )
    customer_feedback = models.TextField(blank=True, verbose_name='نظر مشتری')
    rated_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ثبت رضایت')

    class Meta:
        verbose_name = 'درخواست تعمیر'
        verbose_name_plural = 'درخواست‌های تعمیر'
        ordering = ['-received_at']

    def __str__(self):
        return f'{self.machine_identifier} - {self.get_status_display()}'

    def get_absolute_url(self):
        return reverse('workshop:service_request_detail', args=[self.pk])

    def get_portal_absolute_url(self):
        return reverse('portal:service_request_detail', args=[self.pk])

    @property
    def needs_rating(self) -> bool:
        return self.status == self.Status.DELIVERED and self.customer_rating is None

    def get_related_contract(self):
        """
        قرارداد مرتبط با این درخواست تعمیر را (در صورت وجود) از مسیر
        درخواست → برآورد قیمت → پیش‌فاکتور → قرارداد پیدا می‌کند. ممکن است
        هیچ قراردادی هنوز وجود نداشته باشد (مثلاً هنوز به مرحله برآورد
        نرسیده) که در این صورت None برمی‌گردد.
        """
        estimate = self.cost_estimates.filter(resulting_quote__isnull=False).select_related(
            'resulting_quote'
        ).first()
        if not estimate:
            return None
        return estimate.resulting_quote.contracts.first()


class ServiceRequestImage(models.Model):
    """تصاویر آپلودشده برای یک درخواست تعمیر (توسط کارکنان داخلی، مثلاً تکنسین)."""

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='images',
                                         verbose_name='درخواست تعمیر')
    image = models.ImageField(upload_to=service_request_upload_path, verbose_name='تصویر')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر درخواست تعمیر'
        verbose_name_plural = 'تصاویر درخواست تعمیر'


def service_request_media_upload_path(instance, filename):
    return f'service_request_media/{instance.service_request_id}/{filename}'


class ServiceRequestMedia(models.Model):
    """
    عکس یا فیلم ارسالی توسط خود مشتری از پرتال، هنگام ثبت درخواست تعمیر
    (مثلاً فیلمی از صدای غیرعادی دستگاه یا عکس قطعه خراب). حداقل یک فایل
    برای ثبت درخواست از پرتال الزامی است تا تکنسین تصویر بهتری از خرابی
    داشته باشد.
    """

    class MediaType(models.TextChoices):
        IMAGE = 'image', 'عکس'
        VIDEO = 'video', 'فیلم'

    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'mp4', 'mov', 'webm', '3gp']

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='customer_media',
                                         verbose_name='درخواست تعمیر')
    file = models.FileField(
        upload_to=service_request_media_upload_path, verbose_name='فایل (عکس یا فیلم)',
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)]
    )
    media_type = models.CharField(max_length=8, choices=MediaType.choices, verbose_name='نوع فایل', blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ارسال')

    class Meta:
        verbose_name = 'رسانه ارسالی مشتری'
        verbose_name_plural = 'رسانه‌های ارسالی مشتری'
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if not self.media_type and self.file:
            ext = self.file.name.rsplit('.', 1)[-1].lower()
            self.media_type = self.MediaType.VIDEO if ext in ('mp4', 'mov', 'webm', '3gp') else self.MediaType.IMAGE
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_media_type_display()} - {self.service_request}'


class TaskAssignment(models.Model):
    """تخصیص یک درخواست تعمیر به تکنسین."""

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='assignments',
                                         verbose_name='درخواست تعمیر')
    technician = models.ForeignKey(Technician, on_delete=models.PROTECT, related_name='assignments',
                                    verbose_name='تکنسین')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(null=True, blank=True, verbose_name='تاریخ پایان')

    class Meta:
        verbose_name = 'تخصیص کار'
        verbose_name_plural = 'تخصیص‌های کار'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.technician} -> {self.service_request}'


class RepairLog(models.Model):
    """گزارش روزانه تعمیر."""

    assignment = models.ForeignKey(TaskAssignment, on_delete=models.CASCADE, related_name='repair_logs',
                                    verbose_name='تخصیص کار')
    date = models.DateField(verbose_name='تاریخ')
    parts_used = models.TextField(blank=True, verbose_name='قطعات مصرفی')
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='ساعت صرف‌شده')
    notes = models.TextField(blank=True, verbose_name='توضیحات')

    class Meta:
        verbose_name = 'گزارش تعمیر'
        verbose_name_plural = 'گزارش‌های تعمیر'
        ordering = ['-date']

    def __str__(self):
        return f'گزارش {self.date} - {self.assignment}'


class FieldService(models.Model):
    """مأموریت خدمات خارج از تعمیرگاه."""

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'برنامه‌ریزی‌شده'
        IN_PROGRESS = 'in_progress', 'در حال انجام'
        DONE = 'done', 'انجام‌شده'

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='field_services',
                                         verbose_name='درخواست تعمیر')
    technician = models.ForeignKey(Technician, on_delete=models.PROTECT, related_name='field_services',
                                    verbose_name='تکنسین')
    address = models.TextField(verbose_name='آدرس')
    date = models.DateField(verbose_name='تاریخ')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED, verbose_name='وضعیت')

    class Meta:
        verbose_name = 'مأموریت خارج از تعمیرگاه'
        verbose_name_plural = 'مأموریت‌های خارج از تعمیرگاه'
        ordering = ['-date']

    def __str__(self):
        return f'{self.address} - {self.date}'


class CostEstimate(models.Model):
    """
    برآورد قیمت تعمیر که توسط تکنسین، پس از بررسی اولیه دستگاه، ثبت می‌شود.
    این مدل حلقه واسط بین «تعمیرگاه» و «فروش» است: مدیر فروش این برآورد را
    بررسی و در صورت تایید، یک پیش‌فاکتور برای مشتری از روی آن می‌سازد.
    گردش کار: مشتری تماس می‌گیرد → درخواست تعمیر ثبت و به تکنسین ارجاع
    می‌شود → تکنسین این برآورد را ثبت می‌کند → مدیر فروش تایید/رد می‌کند →
    در صورت تایید، پیش‌فاکتور ساخته می‌شود.
    """

    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'در انتظار تایید مدیر فروش'
        APPROVED = 'approved', 'تایید شده (پیش‌فاکتور صادر شد)'
        REJECTED = 'rejected', 'رد شده'

    service_request = models.ForeignKey('ServiceRequest', on_delete=models.CASCADE, related_name='cost_estimates',
                                         verbose_name='درخواست تعمیر')
    estimated_cost = models.DecimalField(max_digits=16, decimal_places=0, verbose_name='برآورد هزینه (ریال)')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='برآورد ساعت کار')
    parts_needed = models.TextField(blank=True, verbose_name='قطعات مورد نیاز (برآوردی)')
    notes = models.TextField(blank=True, verbose_name='توضیحات فنی تکنسین')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED, verbose_name='وضعیت')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='cost_estimates_created', verbose_name='ثبت‌شده توسط (تکنسین)')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='cost_estimates_reviewed', verbose_name='بررسی‌شده توسط')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ بررسی')
    resulting_quote = models.ForeignKey('sales.Quote', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='source_estimate', verbose_name='پیش‌فاکتور ساخته‌شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')

    class Meta:
        verbose_name = 'برآورد قیمت تعمیر'
        verbose_name_plural = 'برآوردهای قیمت تعمیر'
        ordering = ['-created_at']

    def __str__(self):
        return f'برآورد {self.estimated_cost:,.0f} ریال برای {self.service_request}'

    def get_absolute_url(self):
        return reverse('workshop:cost_estimate_detail', args=[self.pk])
