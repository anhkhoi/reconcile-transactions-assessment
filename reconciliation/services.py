"""CSV import and persisted payout-reconciliation workflows."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import BinaryIO, TextIO

from django.core.exceptions import ValidationError
from django.db import transaction

from reconciliation.models import Order, Payout, ReconciliationResult


REQUIRED_PAYOUT_HEADERS = ("provider", "order_number", "amount", "currency")


class PayoutImportValidationError(ValueError):
    """A client-safe validation error raised before a payout import commits."""


@dataclass(frozen=True)
class PayoutInput:
    """A normalized, validated payout row that has not yet been persisted."""

    provider: str
    order_number: str
    amount: Decimal
    currency: str


def import_payout_csv(uploaded_file: BinaryIO | TextIO) -> int:
    """Validate, persist, and reconcile every payout in an uploaded CSV."""
    payout_inputs = parse_payout_csv(uploaded_file)

    with transaction.atomic():
        orders_by_number = Order.objects.in_bulk(
            (payout.order_number for payout in payout_inputs),
            field_name="order_number",
        )

        for payout_input in payout_inputs:
            payout = Payout.objects.create(
                provider=payout_input.provider,
                order_number=payout_input.order_number,
                amount=payout_input.amount,
                currency=payout_input.currency,
            )
            ReconciliationResult.objects.create(
                payout=payout,
                status=determine_reconciliation_status(
                    payout_input,
                    orders_by_number.get(payout_input.order_number),
                ),
            )

    return len(payout_inputs)


def parse_payout_csv(uploaded_file: BinaryIO | TextIO) -> list[PayoutInput]:
    """Read and validate all payout rows without changing database state."""
    content = uploaded_file.read()
    csv_text = _decode_csv_content(content)
    if not csv_text.strip():
        raise PayoutImportValidationError("The CSV file is empty.")

    try:
        reader = csv.DictReader(StringIO(csv_text))
        if tuple(reader.fieldnames or ()) != REQUIRED_PAYOUT_HEADERS:
            raise PayoutImportValidationError(
                "CSV header must be: provider,order_number,amount,currency"
            )
        return _parse_payout_rows(reader)
    except csv.Error as error:
        raise PayoutImportValidationError("The CSV file is malformed.") from error


def determine_reconciliation_status(
    payout: PayoutInput, order: Order | None
) -> ReconciliationResult.Status:
    """Apply the documented missing-order, currency, amount, and match precedence."""
    if order is None:
        return ReconciliationResult.Status.MISSING_ORDER
    if payout.currency != order.currency:
        return ReconciliationResult.Status.CURRENCY_MISMATCH
    if payout.amount != order.total_amount:
        return ReconciliationResult.Status.AMOUNT_MISMATCH
    return ReconciliationResult.Status.MATCHED


def _decode_csv_content(content: bytes | str) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, bytes):
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise PayoutImportValidationError("CSV file must be UTF-8 encoded.") from error
    raise PayoutImportValidationError("CSV file content could not be read.")


def _parse_payout_rows(reader: csv.DictReader) -> list[PayoutInput]:
    payouts: list[PayoutInput] = []

    for line_number, row in enumerate(reader, start=2):
        if None in row:
            raise PayoutImportValidationError(
                f"Line {line_number}: unexpected extra column value."
            )

        provider = (row.get("provider") or "").strip()
        order_number = (row.get("order_number") or "").strip()
        amount_text = (row.get("amount") or "").strip()
        currency = (row.get("currency") or "").strip()

        if not all((provider, order_number, amount_text, currency)):
            raise PayoutImportValidationError(
                f"Line {line_number}: all fields are required."
            )

        try:
            amount = Decimal(amount_text)
        except InvalidOperation as error:
            raise PayoutImportValidationError(
                f"Line {line_number}: amount is invalid."
            ) from error

        payout = Payout(
            provider=provider,
            order_number=order_number,
            amount=amount,
            currency=currency,
        )
        try:
            payout.full_clean()
        except ValidationError as error:
            messages = "; ".join(
                message for errors in error.message_dict.values() for message in errors
            )
            raise PayoutImportValidationError(
                f"Line {line_number}: {messages}"
            ) from error

        payouts.append(
            PayoutInput(
                provider=provider,
                order_number=order_number,
                amount=amount,
                currency=currency,
            )
        )

    if not payouts:
        raise PayoutImportValidationError("The CSV file has no payout rows.")

    return payouts
