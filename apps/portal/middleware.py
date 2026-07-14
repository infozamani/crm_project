"""
میان‌افزار محدودسازی دسترسی حساب‌های پرتال مشتری: کاربرانی که نقش «مشتری»
دارند فقط اجازه دسترسی به مسیرهای پرتال (/portal/)، صفحه ورود/خروج، و
فایل‌های استاتیک/مدیا را دارند. تلاش برای دسترسی به هر بخش مدیریتی داخلی
دیگر به داشبورد پرتال هدایت می‌شود.
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

ALLOWED_PREFIXES = ('/portal/', '/accounts/', '/static/', '/media/')


class CustomerPortalAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and getattr(user, 'is_customer', False):
            path = request.path
            if not path.startswith(ALLOWED_PREFIXES):
                messages.info(request, 'حساب شما مربوط به پرتال مشتری است.')
                return redirect(reverse('portal:dashboard'))
        return self.get_response(request)
