"""Load the supplied local orders CSV into the source-of-truth order table."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from reconciliation.models import Order


REQUIRED_HEADERS = ("order_number", "total_amount", "currency")


class Command(BaseCommand):
    help = "Seed orders from the supplied CSV file."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--file",
            dest="source_file",
            help="Path to an orders CSV. Defaults to requirements/orders.csv.",
        )

    def handle(self, *args, **options) -> None:
        source_file = Path(
            options["source_file"] or settings.BASE_DIR / "requirements" / "orders.csv"
        )
        orders = self._load_orders(source_file)

        with transaction.atomic():
            for order in orders:
                Order.objects.update_or_create(
                    order_number=order.order_number,
                    defaults={
                        "total_amount": order.total_amount,
                        "currency": order.currency,
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(orders)} orders."))

    def _load_orders(self, source_file: Path) -> list[Order]:
        if not source_file.is_file():
            raise CommandError(f"Orders CSV does not exist: {source_file}")

        try:
            with source_file.open(encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                if tuple(reader.fieldnames or ()) != REQUIRED_HEADERS:
                    raise CommandError(
                        "Orders CSV header must be: order_number,total_amount,currency"
                    )
                return self._parse_rows(reader)
        except OSError as error:
            raise CommandError(f"Could not read orders CSV: {source_file}") from error

    def _parse_rows(self, reader: csv.DictReader) -> list[Order]:
        orders: list[Order] = []
        order_numbers: set[str] = set()

        for line_number, row in enumerate(reader, start=2):
            order_number = (row.get("order_number") or "").strip()
            amount_text = (row.get("total_amount") or "").strip()
            currency = (row.get("currency") or "").strip()

            if not all((order_number, amount_text, currency)):
                raise CommandError(f"Line {line_number}: all fields are required.")
            if order_number in order_numbers:
                raise CommandError(f"Line {line_number}: duplicate order number.")

            try:
                total_amount = Decimal(amount_text)
            except InvalidOperation as error:
                raise CommandError(f"Line {line_number}: total_amount is invalid.") from error

            order = Order(
                order_number=order_number,
                total_amount=total_amount,
                currency=currency,
            )
            try:
                order.full_clean(validate_unique=False)
            except ValidationError as error:
                messages = "; ".join(
                    message for errors in error.message_dict.values() for message in errors
                )
                raise CommandError(f"Line {line_number}: {messages}") from error

            order_numbers.add(order_number)
            orders.append(order)

        if not orders:
            raise CommandError("Orders CSV is empty.")

        return orders
