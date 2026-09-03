from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from reconciliation.models import Order, Payout, ReconciliationResult
from reconciliation.services import (
    PayoutImportValidationError,
    PayoutInput,
    determine_reconciliation_status,
    import_payout_csv,
)


class PayoutImportServiceTests(TestCase):
    def test_import_persists_all_sample_reconciliation_statuses(self) -> None:
        call_command("seed_orders")

        with self._sample_payout_file().open("rb") as payout_file:
            imported_count = import_payout_csv(payout_file)

        self.assertEqual(imported_count, 9)
        self.assertEqual(Payout.objects.count(), 9)
        self.assertEqual(ReconciliationResult.objects.count(), 9)
        statuses = dict(
            ReconciliationResult.objects.values_list("payout__order_number", "status")
        )
        self.assertEqual(statuses["100003"], ReconciliationResult.Status.AMOUNT_MISMATCH)
        self.assertEqual(statuses["100009"], ReconciliationResult.Status.CURRENCY_MISMATCH)
        self.assertEqual(statuses["100011"], ReconciliationResult.Status.MISSING_ORDER)
        self.assertEqual(statuses["100012"], ReconciliationResult.Status.MISSING_ORDER)

    def test_decimal_equal_amounts_are_matched(self) -> None:
        Order.objects.create(
            order_number="100001",
            total_amount=Decimal("0.30"),
            currency="USD",
        )

        imported_count = import_payout_csv(
            self._csv_file("Stripe,100001,0.30,USD")
        )

        result = ReconciliationResult.objects.get()
        self.assertEqual(imported_count, 1)
        self.assertEqual(result.status, ReconciliationResult.Status.MATCHED)
        self.assertEqual(result.payout.amount, Decimal("0.30"))

    def test_currency_mismatch_takes_precedence_over_amount_mismatch(self) -> None:
        order = Order.objects.create(
            order_number="100001",
            total_amount=Decimal("10.00"),
            currency="USD",
        )
        payout = PayoutInput(
            provider="Stripe",
            order_number="100001",
            amount=Decimal("11.00"),
            currency="CAD",
        )

        status = determine_reconciliation_status(payout, order)

        self.assertEqual(status, ReconciliationResult.Status.CURRENCY_MISMATCH)

    def test_invalid_row_leaves_no_partial_import(self) -> None:
        Order.objects.create(
            order_number="100001",
            total_amount=Decimal("125.00"),
            currency="USD",
        )

        with self.assertRaisesRegex(
            PayoutImportValidationError, "Line 3: amount is invalid."
        ):
            import_payout_csv(
                self._csv_file(
                    "Stripe,100001,125.00,USD\nStripe,100002,not-a-decimal,USD"
                )
            )

        self.assertEqual(Payout.objects.count(), 0)
        self.assertEqual(ReconciliationResult.objects.count(), 0)

    def test_invalid_header_is_rejected_before_import(self) -> None:
        with self.assertRaisesRegex(PayoutImportValidationError, "CSV header must be"):
            import_payout_csv(
                BytesIO(b"order_number,amount,currency\n100001,125.00,USD\n")
            )

        self.assertEqual(Payout.objects.count(), 0)

    def test_reupload_creates_new_payout_records(self) -> None:
        Order.objects.create(
            order_number="100001",
            total_amount=Decimal("125.00"),
            currency="USD",
        )

        import_payout_csv(self._csv_file("Stripe,100001,125.00,USD"))
        import_payout_csv(self._csv_file("Stripe,100001,125.00,USD"))

        self.assertEqual(Payout.objects.count(), 2)
        self.assertEqual(ReconciliationResult.objects.count(), 2)

    @staticmethod
    def _csv_file(rows: str) -> BytesIO:
        return BytesIO(
            f"provider,order_number,amount,currency\n{rows}\n".encode("utf-8")
        )

    @staticmethod
    def _sample_payout_file() -> Path:
        return settings.BASE_DIR / "requirements" / "payouts.csv"
