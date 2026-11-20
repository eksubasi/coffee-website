import logging
from threading import Thread

from django.conf import settings
from django.core.mail import EmailMessage

from .pdf import render_invoice_pdf

logger = logging.getLogger(__name__)


def send_invoice_email(invoice):
    """Send the invoice snapshot and its PDF to the recorded customer."""
    message = EmailMessage(
        subject=f"Your Brewnook invoice #{invoice.number}",
        body=(
            f"Hello {invoice.customer_name or 'Customer'},\n\n"
            f"Thank you for your order #{invoice.order_id}.\n"
            f"Invoice: {invoice.number}\n"
            f"Total: {invoice.total:.2f} {invoice.currency}\n\n"
            "Your invoice PDF is attached.\n\n"
            "Brewnook"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.customer_email],
    )
    message.attach(
        f"{invoice.number}.pdf",
        render_invoice_pdf(invoice),
        "application/pdf",
    )

    if message.send(fail_silently=False) != 1:
        raise RuntimeError("Invoice email was not accepted by the email backend.")


def _send_in_background(invoice):
    try:
        send_invoice_email(invoice)
    except Exception:
        logger.exception(
            "Invoice email failed: invoice_id=%s",
            invoice.pk,
        )


def queue_invoice_email(invoice):
    """Start delivery without waiting for PDF rendering or SMTP."""
    try:
        Thread(
            target=_send_in_background,
            args=(invoice,),
            name=f"invoice-email-{invoice.pk}",
            daemon=True,
        ).start()
    except Exception:
        logger.exception(
            "Invoice email could not start: invoice_id=%s",
            invoice.pk,
        )