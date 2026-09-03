"""HTTP views for payout import and persisted reconciliation results."""

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from reconciliation.models import ReconciliationResult
from reconciliation.serializers import (
    PayoutUploadSerializer,
    ReconciliationResultSerializer,
)
from reconciliation.services import PayoutImportValidationError, import_payout_csv


class PayoutUploadView(APIView):
    """Accept a multipart payout CSV and delegate its import to the service."""

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request) -> Response:
        serializer = PayoutUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            imported_count = import_payout_csv(serializer.validated_data["file"])
        except PayoutImportValidationError as error:
            return Response(
                {"file": [str(error)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"imported_count": imported_count},
            status=status.HTTP_201_CREATED,
        )


class ReconciliationListView(APIView):
    """Return persisted reconciliation results without recalculating them."""

    def get(self, request) -> Response:
        results = ReconciliationResult.objects.select_related("payout").order_by(
            "payout__order_number", "pk"
        )
        serializer = ReconciliationResultSerializer(results, many=True)
        return Response(serializer.data)
