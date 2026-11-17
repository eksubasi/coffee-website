from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from pypdf import PdfReader
from rest_framework.test import APIClient

from accounts.models import User
from cart.models import Cart, CartItem
from catalog.models import Category, Product
from invoices.models import Invoice
from invoices.services import create_invoice
from orders.checkout import CheckoutError, checkout
from orders.models import Order
from payments.models import PaymentToken

pytestmark = pytest.mark.django_db


@pytest.fixture
def purchase():
    user = User.objects.create_user(
        email="invoice@example.com",
        password="test-password",
        full_name="Çağrı Şahin",
        tax_id="12345678901",
        home_address="Şişli, İstanbul",
    )
    category = Category.objects.create(name="Invoice Coffee")
    product = Product.objects.create(
        name="Türk Kahvesi",
        model="INV-TEST",
        serial_number="LOT-INV",
        description="Test coffee",
        quantity_in_stock=10,
        price=Decimal("120.50"),
        distributor_name="Test Distributor",
        category=category,
    )
    token = PaymentToken.objects.create(
        user=user,
        last4="4242",
        token="invoice-test-token",
    )
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)

    return user, product, token


def buy(purchase):
    user, _, token = purchase
    return checkout(user, user.home_address, token)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_checkout_creates_invoice_with_correct_total(purchase):
    order = buy(purchase)
    invoice = order.invoice

    assert invoice.total == order.total_price == Decimal("241.00")
    assert invoice.line_items[0]["quantity"] == 2
    assert invoice.line_items[0]["unit_price"] == "120.50"
    assert invoice.line_items[0]["line_total"] == "241.00"
    assert invoice.tax_id == "12345678901"


def test_invoice_creation_is_idempotent(purchase):
    order = buy(purchase)

    assert create_invoice(order).pk == order.invoice.pk
    assert Invoice.objects.filter(order=order).count() == 1


def test_invoice_preserves_customer_and_product_snapshot(purchase):
    user, product, _ = purchase
    invoice = buy(purchase).invoice

    user.full_name = "Changed Name"
    user.home_address = "Changed Address"
    user.tax_id = "99999999999"
    user.save()

    product.name = "Changed Product"
    product.price = Decimal("999.00")
    product.save()

    invoice.refresh_from_db()

    assert invoice.customer_name == "Çağrı Şahin"
    assert invoice.billing_address == "Şişli, İstanbul"
    assert invoice.tax_id == "12345678901"
    assert invoice.line_items[0]["name"] == "Türk Kahvesi"
    assert invoice.total == Decimal("241.00")


def test_owner_downloads_readable_pdf_with_turkish_text(purchase):
    user, _, _ = purchase
    invoice = buy(purchase).invoice

    response = client_for(user).get(
        f"/api/invoices/{invoice.pk}/pdf"
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert "no-store" in response["Cache-Control"]

    reader = PdfReader(BytesIO(response.content))
    text = "\n".join(page.extract_text() for page in reader.pages)

    assert invoice.number in text
    assert "241.00" in text
    assert "120.50" in text
    assert "Çağrı Şahin" in text
    assert "Türk Kahvesi" in text
    assert "Şişli, İstanbul" in text


@pytest.mark.parametrize(
    "role",
    [
        User.Role.SALES_MANAGER,
        User.Role.PRODUCT_MANAGER,
    ],
)
def test_managers_can_download_invoice(purchase, role):
    invoice = buy(purchase).invoice
    manager = User.objects.create_user(
        email=f"{role}@invoice.test",
        password="x",
        role=role,
    )

    response = client_for(manager).get(
        f"/api/invoices/{invoice.pk}/pdf"
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "role",
    [
        User.Role.CUSTOMER,
        User.Role.SUPPORT_AGENT,
    ],
)
def test_other_customer_and_support_agent_are_denied(purchase, role):
    invoice = buy(purchase).invoice
    other = User.objects.create_user(
        email=f"{role}@other.test",
        password="x",
        role=role,
    )

    response = client_for(other).get(
        f"/api/invoices/{invoice.pk}/pdf"
    )

    assert response.status_code == 403


def test_guest_is_denied(purchase):
    invoice = buy(purchase).invoice

    response = APIClient().get(f"/api/invoices/{invoice.pk}/pdf")

    assert response.status_code == 401


def test_unknown_invoice_returns_404(purchase):
    user, _, _ = purchase

    response = client_for(user).get("/api/invoices/999999/pdf")

    assert response.status_code == 404


def test_checkout_response_includes_invoice_link(purchase):
    user, _, token = purchase

    response = client_for(user).post(
        "/api/checkout",
        {
            "payment_token": token.token,
            "address": user.home_address,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["invoice_id"] is not None
    assert response.data["invoice_pdf_url"] == (
        f"/api/invoices/{response.data['invoice_id']}/pdf"
    )


def test_failed_checkout_does_not_create_invoice(purchase):
    _, product, _ = purchase
    product.quantity_in_stock = 1
    product.save()

    with pytest.raises(CheckoutError):
        buy(purchase)

    assert not Invoice.objects.exists()
    assert not Order.objects.exists()


def test_invoice_failure_rolls_back_order_and_stock(purchase):
    _, product, _ = purchase

    with patch(
        "orders.checkout.create_invoice",
        side_effect=RuntimeError("invoice creation failed"),
    ):
        with pytest.raises(RuntimeError):
            buy(purchase)

    product.refresh_from_db()

    assert product.quantity_in_stock == 10
    assert not Order.objects.exists()
    assert not Invoice.objects.exists()
    assert CartItem.objects.count() == 1