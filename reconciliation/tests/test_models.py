from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from reconciliation.models import Order, Payout, ReconciliationResult


class OrderModelTests(TestCase):
    def test_order_number_is_unique(self) -> None:
        Order.objects.create(
            order_number="100001",
            total_amount=Decimal("125.00"),
            currency="USD",
        )

        with self.assertRaises(IntegrityError):
            Order.objects.create(
                order_number="100001",
                total_amount=Decimal("125.00"),
                currency="USD",
            )

    def test_order_amount_is_stored_as_decimal(self) -> None:
        order = Order.objects.create(
            order_number="000123",
            total_amount=Decimal("10.10"),
            currency="USD",
        )

        order.refresh_from_db()

        self.assertEqual(order.order_number, "000123")
        self.assertEqual(order.total_amount, Decimal("10.10"))

    def test_currency_must_be_an_uppercase_three_letter_code(self) -> None:
        order = Order(
            order_number="100001",
            total_amount=Decimal("125.00"),
            currency="usd",
        )

        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_negative_amount_is_rejected_by_database_constraint(self) -> None:
        with self.assertRaises(IntegrityError):
            Order.objects.create(
                order_number="100001",
                total_amount=Decimal("-0.01"),
                currency="USD",
            )


class ReconciliationResultModelTests(TestCase):
    def test_payout_has_at_most_one_reconciliation_result(self) -> None:
        payout = Payout.objects.create(
            provider="Stripe",
            order_number="100001",
            amount=Decimal("125.00"),
            currency="USD",
        )
        ReconciliationResult.objects.create(
            payout=payout,
            status=ReconciliationResult.Status.MATCHED,
        )

        with self.assertRaises(IntegrityError):
            ReconciliationResult.objects.create(
                payout=payout,
                status=ReconciliationResult.Status.AMOUNT_MISMATCH,
            )
