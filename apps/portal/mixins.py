from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class CustomerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    اطمینان از اینکه کاربر لاگین‌کرده یک «مشتری» با رکورد Customer مرتبط
    است. سایر کاربران (کارکنان داخلی) به پرتال مشتری هدایت نمی‌شوند و پیام
    مناسب دریافت می‌کنند.
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_customer and hasattr(user, 'customer_record')

    def handle_no_permission(self):
        from django.contrib import messages
        from django.shortcuts import redirect
        if self.request.user.is_authenticated:
            messages.error(self.request, 'این بخش فقط برای حساب‌های پرتال مشتری در دسترس است.')
            return redirect('reports:dashboard')
        return super().handle_no_permission()
