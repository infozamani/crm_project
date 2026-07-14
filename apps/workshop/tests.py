"""تست‌های واحد برای گردش کار برآورد قیمت (تکنسین → مدیر فروش → پیش‌فاکتور)."""
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase, Client
from django.utils import timezone

from apps.customers.models import Customer
from apps.sales.models import Quote
from apps.users.models import User, Role
from apps.workshop.models import ServiceRequest, Technician, TaskAssignment, CostEstimate


class CostEstimateWorkflowTests(TestCase):
    """تست کامل گردش کار: ثبت درخواست → ارجاع به تکنسین → برآورد → تایید → پیش‌فاکتور."""

    def setUp(self):
        from django.core.management import call_command
        call_command('setup_groups', verbosity=0)

        self.customer = Customer.objects.create(
            name='مشتری تست گردش کار', national_or_economic_id='5551112223', phone_number='09120000001'
        )
        self.sales_manager = User.objects.create_user(
            username='mgr_test', password='pass12345', role=Role.SALES_MANAGER
        )
        self.sales_manager.groups.add(Group.objects.get(name=Role.SALES_MANAGER.label))

        self.tech_user = User.objects.create_user(
            username='tech_test', password='pass12345', role=Role.TECHNICIAN
        )
        self.tech_user.groups.add(Group.objects.get(name=Role.TECHNICIAN.label))
        self.technician = Technician.objects.create(user=self.tech_user, specialty='برق‌کار')

        self.service_request = ServiceRequest.objects.create(
            customer=self.customer, machine_identifier='LDR-TEST', fault_type='برق',
            status=ServiceRequest.Status.PENDING_REVIEW,
        )
        self.assignment = TaskAssignment.objects.create(
            service_request=self.service_request, technician=self.technician,
            start_date=timezone.now().date(),
        )

    def test_technician_can_submit_estimate(self):
        client = Client()
        client.login(username='tech_test', password='pass12345')
        resp = client.post(f'/workshop/{self.service_request.pk}/estimates/new/', {
            'estimated_cost': '20000000', 'estimated_hours': '2', 'parts_needed': '', 'notes': ''
        })
        self.assertEqual(resp.status_code, 302)
        estimate = CostEstimate.objects.get(service_request=self.service_request)
        self.assertEqual(estimate.status, CostEstimate.Status.SUBMITTED)
        self.assertEqual(estimate.created_by, self.tech_user)

    def test_sales_manager_approval_creates_quote(self):
        estimate = CostEstimate.objects.create(
            service_request=self.service_request, estimated_cost=Decimal('15000000'),
            estimated_hours=Decimal('3'), created_by=self.tech_user,
        )
        client = Client()
        client.login(username='mgr_test', password='pass12345')
        resp = client.get(f'/workshop/estimates/{estimate.pk}/approve/')
        self.assertEqual(resp.status_code, 302)

        estimate.refresh_from_db()
        self.assertEqual(estimate.status, CostEstimate.Status.APPROVED)
        self.assertIsNotNone(estimate.resulting_quote)
        self.assertEqual(estimate.reviewed_by, self.sales_manager)

        quote = Quote.objects.get(pk=estimate.resulting_quote.pk)
        self.assertEqual(quote.items.count(), 1)
        self.assertEqual(quote.opportunity.customer, self.customer)

    def test_technician_cannot_approve_estimate(self):
        """تکنسین نباید بتواند برآورد خودش را تایید کند (فقط مدیر فروش/مدیرعامل)."""
        estimate = CostEstimate.objects.create(
            service_request=self.service_request, estimated_cost=Decimal('10000000'),
            created_by=self.tech_user,
        )
        client = Client()
        client.login(username='tech_test', password='pass12345')
        resp = client.get(f'/workshop/estimates/{estimate.pk}/approve/')
        self.assertEqual(resp.status_code, 403)


class PortalMediaRequirementTests(TestCase):
    """تست الزامی بودن عکس/فیلم هنگام ثبت درخواست تعمیر از پرتال مشتری."""

    def setUp(self):
        self.customer = Customer.objects.create(
            name='مشتری پرتال', national_or_economic_id='7778889990', phone_number='09123334444'
        )
        self.portal_user = User.objects.create_user(
            username='portal_cust', password='pass12345', role=Role.CUSTOMER
        )
        self.customer.portal_user = self.portal_user
        self.customer.save()

    def test_service_request_creation_fails_without_media(self):
        client = Client()
        client.login(username='portal_cust', password='pass12345')
        resp = client.post('/portal/service-requests/new/', {
            'machine_identifier': 'X-1', 'fault_type': 'موتور',
            'description': 'صدای عجیب',
            'customer_media-TOTAL_FORMS': '2',
            'customer_media-INITIAL_FORMS': '0',
            'customer_media-MIN_NUM_FORMS': '1',
            'customer_media-MAX_NUM_FORMS': '1000',
        })
        # بدون فایل، فرم نباید معتبر باشد و درخواستی نباید ساخته شود
        self.assertEqual(ServiceRequest.objects.filter(machine_identifier='X-1').count(), 0)

    def test_service_request_creation_succeeds_with_media(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        client = Client()
        client.login(username='portal_cust', password='pass12345')
        tiny_gif = (
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        image = SimpleUploadedFile('test.jpg', tiny_gif, content_type='image/jpeg')
        resp = client.post('/portal/service-requests/new/', {
            'machine_identifier': 'X-2', 'fault_type': 'موتور', 'description': 'صدای عجیب',
            'customer_media-TOTAL_FORMS': '2',
            'customer_media-INITIAL_FORMS': '0',
            'customer_media-MIN_NUM_FORMS': '1',
            'customer_media-MAX_NUM_FORMS': '1000',
            'customer_media-0-file': image,
        })
        self.assertTrue(ServiceRequest.objects.filter(machine_identifier='X-2').exists())


class ServiceRequestRatingTests(TestCase):
    """تست رضایت‌سنجی مشتری پس از تحویل دستگاه."""

    def setUp(self):
        self.customer = Customer.objects.create(
            name='مشتری رضایت‌سنجی', national_or_economic_id='1112223334', phone_number='09121110000'
        )
        self.portal_user = User.objects.create_user(
            username='rating_cust', password='pass12345', role=Role.CUSTOMER
        )
        self.customer.portal_user = self.portal_user
        self.customer.save()
        self.sr = ServiceRequest.objects.create(
            customer=self.customer, machine_identifier='R-1', fault_type='ترمز',
            status=ServiceRequest.Status.DELIVERED,
        )

    def test_needs_rating_true_before_rating(self):
        self.assertTrue(self.sr.needs_rating)

    def test_customer_can_submit_rating(self):
        client = Client()
        client.login(username='rating_cust', password='pass12345')
        resp = client.post(f'/portal/service-requests/{self.sr.pk}/rate/', {
            'customer_rating': 5, 'customer_feedback': 'عالی بود'
        })
        self.assertEqual(resp.status_code, 302)
        self.sr.refresh_from_db()
        self.assertEqual(self.sr.customer_rating, 5)
        self.assertFalse(self.sr.needs_rating)
        self.assertIsNotNone(self.sr.rated_at)
