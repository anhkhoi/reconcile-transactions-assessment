"""Request validation and response serialization for reconciliation APIs."""

from django.conf import settings
from rest_framework import serializers

from reconciliation.models import ReconciliationResult


class PayoutUploadSerializer(serializers.Serializer):
    """Validate upload metadata before the service reads a payout CSV."""

    file = serializers.FileField(write_only=True)

    def validate_file(self, uploaded_file):
        if uploaded_file.size > settings.PAYOUT_UPLOAD_MAX_BYTES:
            raise serializers.ValidationError(
                "File exceeds the maximum allowed upload size."
            )

        content_type = getattr(uploaded_file, "content_type", None)
        if content_type and content_type not in {"text/csv", "application/csv"}:
            raise serializers.ValidationError("File content type must be text/csv.")

        return uploaded_file


class ReconciliationResultSerializer(serializers.ModelSerializer):
    """Expose only persisted reconciliation fields intended for API consumers."""

    order_number = serializers.CharField(source="payout.order_number")

    class Meta:
        model = ReconciliationResult
        fields = ("order_number", "status")
