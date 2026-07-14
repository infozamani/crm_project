from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.users.models import Role, User

from .forms import CustomerForm, SalesOpportunityForm, InteractionForm
from .models import Customer, SalesOpportunity, Interaction


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q')
        customer_type = self.request.GET.get('type')
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(national_or_economic_id__icontains=query) |
                Q(phone_number__icontains=query)
            )
        if customer_type:
            qs = qs.filter(customer_type=customer_type)
        return qs


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.add_customer'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'مشتری با موفقیت ثبت شد.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'لطفاً خطاهای فرم را برطرف کنید.')
        return super().form_invalid(form)


class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.change_customer'

    def form_valid(self, form):
        messages.success(self.request, 'اطلاعات مشتری به‌روزرسانی شد.')
        return super().form_valid(form)


class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customers:customer_list')
    permission_required = 'customers.delete_customer'

    def form_valid(self, form):
        messages.success(self.request, 'مشتری حذف شد.')
        return super().form_valid(form)


class OpportunityListView(LoginRequiredMixin, ListView):
    model = SalesOpportunity
    template_name = 'customers/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer', 'owner')
        status = self.request.GET.get('status')
        customer_id = self.request.GET.get('customer')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        # کارشناس فروش فقط فرصت‌های خودش را می‌بیند، مگر آنکه مدیر/مدیرعامل باشد
        user = self.request.user
        if not (user.is_superuser or user.is_ceo or user.is_sales_manager):
            qs = qs.filter(owner=user)

        if status:
            qs = qs.filter(status=status)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = SalesOpportunity.Status.choices
        ctx['customers'] = Customer.objects.all()
        return ctx


class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = SalesOpportunity
    template_name = 'customers/opportunity_detail.html'
    context_object_name = 'opportunity'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['interaction_form'] = InteractionForm()
        return ctx


class OpportunityCreateView(LoginRequiredMixin, CreateView):
    model = SalesOpportunity
    form_class = SalesOpportunityForm
    template_name = 'customers/opportunity_form.html'

    def form_valid(self, form):
        if not form.instance.owner_id:
            form.instance.owner = self.request.user
        messages.success(self.request, 'فرصت فروش جدید ثبت شد.')
        return super().form_valid(form)


class OpportunityUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesOpportunity
    form_class = SalesOpportunityForm
    template_name = 'customers/opportunity_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'فرصت فروش به‌روزرسانی شد.')
        return super().form_valid(form)


class InteractionCreateView(LoginRequiredMixin, CreateView):
    model = Interaction
    form_class = InteractionForm
    template_name = 'customers/interaction_form.html'

    def form_valid(self, form):
        form.instance.opportunity_id = self.kwargs['opportunity_pk']
        form.instance.created_by = self.request.user
        messages.success(self.request, 'تعامل جدید ثبت شد.')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.opportunity.get_absolute_url()


class CreatePortalAccountView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    ایجاد یک حساب کاربری پرتال مشتری برای یک مشتری موجود، مستقیماً از داخل
    برنامه (معادل اکشن create_portal_accounts در پنل ادمین). فقط کاربرانی که
    اجازه ویرایش مشتری را دارند می‌توانند این کار را انجام دهند.
    """
    permission_required = 'customers.change_customer'

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        if customer.portal_user_id:
            messages.warning(request, 'این مشتری از قبل حساب پرتال دارد.')
            return redirect(customer.get_absolute_url())

        username = f'customer{customer.pk}'
        password = get_random_string(10)
        user = User.objects.create_user(
            username=username, password=password,
            first_name=customer.name[:30], role=Role.CUSTOMER, is_staff=False,
        )
        customer.portal_user = user
        customer.save(update_fields=['portal_user'])
        messages.success(
            request,
            f'حساب پرتال مشتری ساخته شد. نام کاربری: «{username}» — رمز عبور: «{password}» '
            f'(این رمز فقط همین یک بار نمایش داده می‌شود؛ لطفاً به مشتری اطلاع دهید.)'
        )
        return redirect(customer.get_absolute_url())
