from django.urls import path

from .views import InvoicePDFView

urlpatterns = [
    path(
        "invoices/<int:pk>/pdf",
        InvoicePDFView.as_view(),
        name="invoice-pdf",
    ),
]