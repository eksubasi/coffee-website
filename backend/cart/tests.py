"""KAN-39: server-side cart and guest cart merge on login (Req 4)."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from cart.models import Cart, CartItem
from catalog.models import Category, Product


@pytest.fixture
def products(db):
    category = Category.objects.create(name="Cart Test")

    def make(model, price, stock):
        return Product.objects.create(
            name=f"Product {model}",
            model=model,
            serial_number=f"SN-{model}",
            description="test",
            quantity_in_stock=stock,
            price=Decimal(price),
            distributor_name="Test Distributor",
            category=category,
        )

    # beans: plenty of stock, grinder: only 3 left, kenya: sold out
    return {
        "beans": make("C1", "100.00", 10),
        "grinder": make("C2", "250.00", 3),
        "kenya": make("C3", "80.00", 0),
    }


@pytest.fixture
def customer(db):
    return User.objects.create_user(email="cart@test.com", password="x")


@pytest.fixture
def api(customer):
    client = APIClient()
    client.force_authenticate(user=customer)
    return client


def quantities(customer):
    return {
        item.product.model: item.quantity
        for item in CartItem.objects.filter(cart__user=customer)
    }


def test_new_customer_gets_empty_cart(api):
    response = api.get("/api/cart")

    assert response.status_code == 200
    assert response.data["items"] == []
    assert Decimal(response.data["total_price"]) == Decimal("0.00")


def test_guest_cart_is_kept_after_login(api, customer, products):
    # Req 4: what the guest added before logging in is still there afterwards
    guest_cart = {"items": [{"product": products["beans"].id, "quantity": 2}]}

    response = api.post("/api/cart/merge", guest_cart, format="json")

    assert response.status_code == 200
    assert quantities(customer) == {"C1": 2}
    assert Decimal(response.data["total_price"]) == Decimal("200.00")


def test_merge_adds_to_existing_cart(api, customer, products):
    cart = Cart.objects.create(user=customer)
    CartItem.objects.create(cart=cart, product=products["beans"], quantity=3)

    api.post(
        "/api/cart/merge",
        {"items": [{"product": products["beans"].id, "quantity": 4}]},
        format="json",
    )

    assert quantities(customer) == {"C1": 7}


def test_merge_caps_quantity_at_stock(api, customer, products):
    api.post(
        "/api/cart/merge",
        {"items": [{"product": products["grinder"].id, "quantity": 5}]},
        format="json",
    )

    assert quantities(customer) == {"C2": 3}


def test_merge_drops_out_of_stock_products(api, customer, products):
    api.post(
        "/api/cart/merge",
        {
            "items": [
                {"product": products["kenya"].id, "quantity": 1},
                {"product": products["beans"].id, "quantity": 1},
            ]
        },
        format="json",
    )

    assert quantities(customer) == {"C1": 1}


def test_put_replaces_cart(api, customer, products):
    api.post(
        "/api/cart/merge",
        {"items": [{"product": products["beans"].id, "quantity": 2}]},
        format="json",
    )

    response = api.put(
        "/api/cart",
        {"items": [{"product": products["grinder"].id, "quantity": 1}]},
        format="json",
    )

    assert response.status_code == 200
    assert quantities(customer) == {"C2": 1}


def test_put_with_quantity_zero_removes_item(api, customer, products):
    api.put(
        "/api/cart",
        {"items": [{"product": products["beans"].id, "quantity": 0}]},
        format="json",
    )

    assert quantities(customer) == {}


def test_delete_empties_cart(api, customer, products):
    api.post(
        "/api/cart/merge",
        {"items": [{"product": products["beans"].id, "quantity": 2}]},
        format="json",
    )

    response = api.delete("/api/cart")

    assert response.status_code == 204
    assert quantities(customer) == {}


def test_unknown_product_is_rejected(api):
    response = api.put(
        "/api/cart", {"items": [{"product": 99999, "quantity": 1}]}, format="json"
    )

    assert response.status_code == 400


def test_cart_requires_login(db):
    assert APIClient().get("/api/cart").status_code == 401


def test_cart_is_customer_only(db):
    manager = User.objects.create_user(
        email="pm@test.com", password="x", role=User.Role.PRODUCT_MANAGER
    )
    client = APIClient()
    client.force_authenticate(user=manager)

    assert client.get("/api/cart").status_code == 403