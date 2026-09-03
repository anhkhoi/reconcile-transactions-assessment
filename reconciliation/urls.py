"""API URLs for the reconciliation application."""

from django.urls import path

from reconciliation.views import PayoutUploadView, ReconciliationListView


urlpatterns = [
    path("payouts/upload", PayoutUploadView.as_view(), name="payout-upload"),
    path("reconciliation", ReconciliationListView.as_view(), name="reconciliation-list"),
]
