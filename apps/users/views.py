from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import UpdateView, TemplateView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .forms import LoginForm, ProfileForm


@method_decorator(ratelimit(key='ip', rate='10/m', block=True), name='post')
class CRMLoginView(LoginView):
    """ورود به سیستم با محدودیت نرخ درخواست برای جلوگیری از Brute Force.
    پس از ورود موفق، بر اساس نقش کاربر (مشتری یا کارمند داخلی) به مقصد
    مناسب هدایت می‌شود."""
    template_name = 'users/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return self.request.user.get_post_login_url()


class CRMLogoutView(LogoutView):
    next_page = 'users:login'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """صفحه «پروفایل من»: ویرایش نام، ایمیل، توضیح کوتاه و عکس پروفایل، بدون
    نیاز به ورود به پنل ادمین."""
    form_class = ProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
        return super().form_valid(form)


class CRMPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """صفحه تغییر رمز عبور، در قالب داخلی برنامه (نه پنل ادمین)."""
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        messages.success(self.request, 'رمز عبور شما با موفقیت تغییر کرد.')
        return super().form_valid(form)


class SettingsView(LoginRequiredMixin, TemplateView):
    """
    منوی «تنظیمات»: نقطه ورود ساده به پروفایل و تغییر رمز، برای کاربرانی که
    آشنایی چندانی با پنل ادمین ندارند.
    """
    template_name = 'users/settings.html'
