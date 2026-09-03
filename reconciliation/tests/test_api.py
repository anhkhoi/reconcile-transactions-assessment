from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from reconciliation.models import Order, Payout, ReconciliationResult


class PayoutUploadApiTests(APITestCase):
    def test_valid_multipart_upload_imports_sample_payouts(self) -> None:
        call_command("seed_orders")

        response = self._upload(self._sample_payout_file().read_bytes())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"imported_count": 9})
        self.assertEqual(Payout.objects.count(), 9)
        self.assertEqual(ReconciliationResult.objects.count(), 9)

    def test_invalid_payout_row_returns_400_without_writing_data(self) -> None:
        response = self._upload(
            b"provider,order_number,amount,currency\n"
            b"Stripe,100001,125.00,USD\n"
            b"Stripe,100002,not-a-decimal,USD\n"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Line 3: amount is invalid.", response.data["file"])
        self.assertEqual(Payout.objects.count(), 0)
        self.assertEqual(ReconciliationResult.objects.count(), 0)

    def test_empty_upload_returns_400_without_writing_data(self) -> None:
        response = self._upload(b"")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payout.objects.count(), 0)
        self.assertEqual(ReconciliationResult.objects.count(), 0)

    def test_non_csv_content_type_is_rejected(self) -> None:
        response = self._upload(b"not a CSV", content_type="application/pdf")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File content type must be text/csv.", response.data["file"])

    @override_settings(PAYOUT_UPLOAD_MAX_BYTES=10)
    def test_oversized_upload_is_rejected(self) -> None:
        response = self._upload(
            b"provider,order_number,amount,currency\nStripe,100001,125.00,USD\n"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File exceeds the maximum allowed upload size.", response.data["file"])

    @staticmethod
    def _sample_payout_file() -> Path:
        return settings.BASE_DIR / "requirements" / "payouts.csv"

    def _upload(self, content: bytes, content_type: str = "text/csv"):
        uploaded_file = SimpleUploadedFile(
            "payouts.csv",
            content,
            content_type=content_type,
        )
        return self.client.post(
            reverse("payout-upload"),
            {"file": uploaded_file},
            format="multipart",
        )


class ReconciliationListApiTests(APITestCase):
    def test_results_return_persisted_statuses_in_stable_order(self) -> None:
        Order.objects.create(
            order_number="100002",
            total_amount=Decimal("20.00"),
            currency="USD",
        )
        Order.objects.create(
            order_number="100001",
            total_amount=Decimal("10.00"),
            currency="USD",
        )

        self._upload("Stripe,100002,20.00,USD\nStripe,100001,10.00,USD")
        Order.objects.filter(order_number="100001").update(total_amount=Decimal("99.00"))

        response = self.client.get(reverse("reconciliation-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {"order_number": "100001", "status": "Matched"},
                {"order_number": "100002", "status": "Matched"},
            ],
        )

    def _upload(self, rows: str):
        uploaded_file = SimpleUploadedFile(
            "payouts.csv",
            f"provider,order_number,amount,currency\n{rows}\n".encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("payout-upload"),
            {"file": uploaded_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
