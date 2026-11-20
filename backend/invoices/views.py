from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User

from .models import Invoice
from .pdf import render_invoice_pdf


class InvoicePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        invoice = get_object_or_404(
            Invoice.objects.select_related("order"),
            pk=pk,
        )

        is_owner = (
            request.user.role == User.Role.CUSTOMER
            and invoice.order.user_id == request.user.pk
        )
        is_manager = request.user.role in {
            User.Role.SALES_MANAGER,
            User.Role.PRODUCT_MANAGER,
        }

        if not (is_owner or is_manager):
            raise PermissionDenied("You cannot access this invoice.")

        response = HttpResponse(
            render_invoice_pdf(invoice),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{invoice.number}.pdf"'
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response