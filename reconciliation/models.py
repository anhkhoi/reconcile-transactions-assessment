"""Persistence models for orders, imported payouts, and their outcomes."""

from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


CURRENCY_VALIDATOR = RegexValidator(
    regex=r"^[A-Z]{3}$",
    message="Currency must be a three-letter uppercase ISO code.",
)
NON_NEGATIVE_AMOUNT = MinValueValidator(Decimal("0"))


class Order(models.Model):
    """The source-of-truth order record used to reconcile a payout."""

    order_number = models.CharField(max_length=64, unique=True)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[NON_NEGATIVE_AMOUNT],
    )
    currency = models.CharField(max_length=3, validators=[CURRENCY_VALIDATOR])

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="order_total_amount_nonnegative",
            )
        ]

    def __str__(self) -> str:
        return self.order_number


class Payout(models.Model):
    """One imported payout CSV row. Re-imports intentionally create new rows."""

    provider = models.CharField(max_length=100)
    order_number = models.CharField(max_length=64, db_index=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[NON_NEGATIVE_AMOUNT],
    )
    currency = models.CharField(max_length=3, validators=[CURRENCY_VALIDATOR])
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="payout_amount_nonnegative",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider}: {self.order_number}"


class ReconciliationResult(models.Model):
    """The persisted outcome assigned to a payout during import."""

    class Status(models.TextChoices):
        MATCHED = "Matched", "Matched"
        MISSING_ORDER = "Missing Order", "Missing Order"
        AMOUNT_MISMATCH = "Amount Mismatch", "Amount Mismatch"
        CURRENCY_MISMATCH = "Currency Mismatch", "Currency Mismatch"

    payout = models.OneToOneField(
        Payout,
        on_delete=models.CASCADE,
        related_name="reconciliation_result",
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.payout.order_number}: {self.status}"
