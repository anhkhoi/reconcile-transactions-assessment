from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from reconciliation.models import Order


class SeedOrdersCommandTests(TestCase):
    def test_seed_orders_imports_the_supplied_source_data(self) -> None:
        output = StringIO()

        call_command("seed_orders", stdout=output)

        self.assertEqual(Order.objects.count(), 10)
        self.assertEqual(
            Order.objects.get(order_number="100003").total_amount,
            Decimal("240.50"),
        )
        self.assertIn("Seeded 10 orders.", output.getvalue())

    def test_seed_orders_updates_existing_order_from_source_data(self) -> None:
        Order.objects.create(
            order_number="100001",
            total_amount=Decimal("1.00"),
            currency="CAD",
        )

        call_command("seed_orders")

        order = Order.objects.get(order_number="100001")
        self.assertEqual(order.total_amount, Decimal("125.00"))
        self.assertEqual(order.currency, "USD")
