from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order, OrderItem


@pytest.fixture
def customer(db):
    return User.objects.create_user(email="buyer@orders.test", password="x")


@pytest.fixture
def products(db):
    category = Category.objects.create(name="Test Beans")

    def make(model, price):
        return Product.objects.create(
            name=f"Product {model}",
            model=model,
            serial_number=f"SN-{model}",
            description="test",
            quantity_in_stock=10,
            price=Decimal(price),
            distributor_name="Test Distributor",
            category=category,
        )

    return [make("P1", "100.00"), make("P2", "250.50")]


@pytest.fixture
def order(customer, products):
    order = Order.objects.create(user=customer, address="1 Coffee Street, Istanbul")
    OrderItem.objects.create(order=order, product=products[0], quantity=2, unit_price=Decimal("100.00"))
    OrderItem.objects.create(order=order, product=products[1], quantity=1, unit_price=Decimal("250.50"))
    return order


@pytest.fixture
def api_as():
    def make(role):
        user = User.objects.create_user(email=f"{role}@orders.test", password="x", role=role)
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return make


@pytest.fixture
def pm(api_as):
    return api_as(User.Role.PRODUCT_MANAGER)
