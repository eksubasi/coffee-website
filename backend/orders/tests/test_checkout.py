"""KAN-41: checkout turns the cart into an order with atomic stock checks."""

import threading
from decimal import Decimal

import pytest
from django.db import connection
from rest_framework.test import APIClient

from accounts.models import User
from cart.models import Cart, CartItem
from catalog.models import Category, Product
from orders.checkout import CheckoutError, checkout
from orders.models import Delivery, Order
from payments.models import PaymentToken


def make_token(user):
    return PaymentToken.objects.create(user=user, last4="4242", token=f"tok-{user.pk}")


def fill_cart(user, *product_quantities):
    cart, _ = Cart.objects.get_or_create(user=user)
    for product, quantity in product_quantities:
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)
    return cart


@pytest.fixture
def api(customer):
    client = APIClient()
    client.force_authenticate(user=customer)
    return client


@pytest.fixture
def token(customer):
    return make_token(customer)


def post_checkout(api, token, address="1 Coffee Street"):
    return api.post(
        "/api/checkout", {"payment_token": token.token, "address": address}, format="json"
    )


# --- Successful checkout -----------------------------------------------------


def test_checkout_creates_order_with_purchase_time_prices(api, customer, products, token):
    fill_cart(customer, (products[0], 2), (products[1], 1))

    response = post_checkout(api, token)

    assert response.status_code == 201
    order = Order.objects.get(user=customer)
    assert order.payment_token == token
    assert order.status == Order.Status.PROCESSING
    assert order.total_price == Decimal("450.50")
    assert {i.product_id: i.unit_price for i in order.items.all()} == {
        products[0].id: Decimal("100.00"),
        products[1].id: Decimal("250.50"),
    }


def test_checkout_decrements_stock_and_increases_popularity(api, customer, products, token):
    fill_cart(customer, (products[0], 3))

    post_checkout(api, token)

    products[0].refresh_from_db()
    assert products[0].quantity_in_stock == 7
    assert products[0].popularity == 3


def test_checkout_empties_cart_and_creates_deliveries(api, customer, products, token):
    fill_cart(customer, (products[0], 1), (products[1], 1))

    post_checkout(api, token)

    assert not CartItem.objects.filter(cart__user=customer).exists()
    assert Delivery.objects.filter(customer=customer).count() == 2


def test_checkout_uses_home_address_when_none_given(api, customer, products, token):
    customer.home_address = "5 Home Road, Istanbul"
    customer.save()
    fill_cart(customer, (products[0], 1))

    response = post_checkout(api, token, address="")

    assert response.status_code == 201
    assert Order.objects.get(user=customer).address == "5 Home Road, Istanbul"


# --- Failures: nothing must change -------------------------------------------


def test_not_enough_stock_fails_whole_order(api, customer, products, token):
    products[1].quantity_in_stock = 1
    products[1].save()
    fill_cart(customer, (products[0], 2), (products[1], 5))

    response = post_checkout(api, token)

    assert response.status_code == 409
    assert response.data["problems"][0]["product"] == products[1].id
    assert not Order.objects.exists()
    products[0].refresh_from_db()
    assert products[0].quantity_in_stock == 10  # first item not decremented either
    assert CartItem.objects.filter(cart__user=customer).count() == 2  # cart kept


def test_empty_cart_cannot_check_out(api, token):
    response = post_checkout(api, token)

    assert response.status_code == 400
    assert not Order.objects.exists()


def test_checkout_requires_own_payment_token(api, customer, products):
    other = User.objects.create_user(email="other@orders.test", password="x")
    fill_cart(customer, (products[0], 1))

    response = post_checkout(api, make_token(other))

    assert response.status_code == 400
    assert not Order.objects.exists()


def test_checkout_requires_an_address(api, customer, products, token):
    fill_cart(customer, (products[0], 1))

    response = post_checkout(api, token, address="")

    assert response.status_code == 400


def test_checkout_is_customer_only(db, pm):
    assert APIClient().post("/api/checkout").status_code == 401
    assert pm.post("/api/checkout").status_code == 403


# --- Req 18: two customers buy the last item at the same time ----------------


@pytest.mark.django_db(transaction=True)
def test_concurrent_checkouts_of_last_item_only_one_succeeds():
    category = Category.objects.create(name="Concurrency")
    guatemala = Product.objects.create(
        name="Guatemala Huehuetenango",
        model="CONC-1",
        serial_number="LOT-CONC",
        description="test",
        quantity_in_stock=1,
        price=Decimal("90.00"),
        distributor_name="Test Distributor",
        category=category,
    )
    buyers = []
    for n in range(2):
        user = User.objects.create_user(email=f"buyer{n}@race.test", password="x")
        fill_cart(user, (guatemala, 1))
        buyers.append((user, make_token(user)))

    start = threading.Barrier(len(buyers))
    results = []

    def buy(user, token):
        try:
            start.wait()  # both threads start checkout at the same moment
            checkout(user, "Race Street 1", token)
            results.append("ok")
        except CheckoutError:
            results.append("out of stock")
        finally:
            connection.close()  # each thread has its own database connection

    threads = [threading.Thread(target=buy, args=b) for b in buyers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == ["ok", "out of stock"]
    guatemala.refresh_from_db()
    assert guatemala.quantity_in_stock == 0
    assert Order.objects.count() == 1