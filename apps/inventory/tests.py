"""تست‌های واحد برای مدل انبار و قطعات یدکی."""
from django.test import TestCase

from apps.inventory.models import Part, InventoryTransaction


class PartStockTests(TestCase):

    def setUp(self):
        self.part = Part.objects.create(
            name='فیلتر روغن', code='FLT-001', brand='CAT', min_stock=5, max_stock=100, unit_price=500000
        )

    def test_current_stock_with_in_and_out_transactions(self):
        InventoryTransaction.objects.create(part=self.part, transaction_type=InventoryTransaction.TransactionType.IN, quantity=20)
        InventoryTransaction.objects.create(part=self.part, transaction_type=InventoryTransaction.TransactionType.OUT, quantity=8)
        self.assertEqual(self.part.current_stock, 12)

    def test_is_below_minimum_true_when_stock_low(self):
        InventoryTransaction.objects.create(part=self.part, transaction_type=InventoryTransaction.TransactionType.IN, quantity=10)
        InventoryTransaction.objects.create(part=self.part, transaction_type=InventoryTransaction.TransactionType.OUT, quantity=7)
        self.assertTrue(self.part.is_below_minimum)

    def test_is_below_minimum_false_when_stock_sufficient(self):
        InventoryTransaction.objects.create(part=self.part, transaction_type=InventoryTransaction.TransactionType.IN, quantity=50)
        self.assertFalse(self.part.is_below_minimum)


from django.contrib.auth.models import Group
from django.test import Client

from apps.users.models import User, Role


class PartRequestWorkflowTests(TestCase):
    """تست گردش کار درخواست قطعه: تکنسین درخواست می‌دهد، انباردار تامین می‌کند."""

    def setUp(self):
        from django.core.management import call_command
        call_command('setup_groups', verbosity=0)

        self.part = Part.objects.create(
            name='رله برق', code='RLY-001', min_stock=2, max_stock=50, unit_price=300000
        )
        InventoryTransaction.objects.create(
            part=self.part, transaction_type=InventoryTransaction.TransactionType.IN, quantity=10
        )

        self.tech_user = User.objects.create_user(username='tech_pr', password='pass12345', role=Role.TECHNICIAN)
        self.tech_user.groups.add(Group.objects.get(name=Role.TECHNICIAN.label))

        self.storekeeper = User.objects.create_user(username='store_pr', password='pass12345', role=Role.STOREKEEPER)
        self.storekeeper.groups.add(Group.objects.get(name=Role.STOREKEEPER.label))

    def test_technician_can_create_part_request(self):
        client = Client()
        client.login(username='tech_pr', password='pass12345')
        resp = client.post('/inventory/part-requests/new/', {
            'part': self.part.id, 'quantity_requested': 3, 'note': 'برای تعمیر لودر'
        })
        self.assertEqual(resp.status_code, 302)
        from apps.inventory.models import PartRequest
        pr = PartRequest.objects.get(part=self.part)
        self.assertEqual(pr.status, PartRequest.Status.PENDING)
        self.assertEqual(pr.requested_by, self.tech_user)

    def test_storekeeper_fulfill_creates_transaction_and_reduces_stock(self):
        from apps.inventory.models import PartRequest
        pr = PartRequest.objects.create(part=self.part, quantity_requested=3, requested_by=self.tech_user)

        stock_before = self.part.current_stock
        client = Client()
        client.login(username='store_pr', password='pass12345')
        resp = client.get(f'/inventory/part-requests/{pr.pk}/fulfill/')
        self.assertEqual(resp.status_code, 302)

        pr.refresh_from_db()
        self.assertEqual(pr.status, PartRequest.Status.FULFILLED)
        self.assertIsNotNone(pr.fulfilled_transaction)
        self.assertEqual(self.part.current_stock, stock_before - 3)

    def test_technician_cannot_fulfill_own_request(self):
        from apps.inventory.models import PartRequest
        pr = PartRequest.objects.create(part=self.part, quantity_requested=1, requested_by=self.tech_user)
        client = Client()
        client.login(username='tech_pr', password='pass12345')
        resp = client.get(f'/inventory/part-requests/{pr.pk}/fulfill/')
        self.assertEqual(resp.status_code, 403)
