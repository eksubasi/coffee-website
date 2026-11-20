"""KAN-56: ratings (1-5), only for delivered purchases, average on the product."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order, OrderItem
from reviews.models import Rating


@pytest.fixture
def product(db):
    category = Category.objects.create(name="Test Beans")
    return Product.objects.create(
        name="Kenya AA",
        model="KEN",
        serial_number="SN-KEN",
        description="test",
        quantity_in_stock=10,
        price=Decimal("590.00"),
        distributor_name="Test Distributor",
        category=category,
    )


def make_customer(email):
    return User.objects.create_user(email=email, password="x")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def buy(user, product, status=Order.Status.DELIVERED):
    order = Order.objects.create(user=user, address="1 Coffee Street", status=status)
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price=product.price)
    return order


def url(product):
    return f"/api/products/{product.id}/my-rating/"


@pytest.fixture
def buyer(product):
    user = make_customer("buyer@reviews.test")
    buy(user, product)
    return user


# --- Who may rate ---------------------------------------------------------------


def test_customer_with_delivered_order_can_rate(buyer, product):
    response = client_for(buyer).put(url(product), {"score": 4}, format="json")

    assert response.status_code == 201
    assert response.data == {"score": 4, "can_rate": True}
    assert Rating.objects.get(user=buyer, product=product).score == 4


@pytest.mark.parametrize(
    "status", [Order.Status.PROCESSING, Order.Status.IN_TRANSIT, Order.Status.CANCELLED]
)
def test_order_not_delivered_cannot_rate(product, status):
    user = make_customer("waiting@reviews.test")
    buy(user, product, status=status)

    response = client_for(user).put(url(product), {"score": 5}, format="json")

    assert response.status_code == 403
    assert not Rating.objects.exists()


def test_customer_who_never_bought_cannot_rate(product):
    user = make_customer("stranger@reviews.test")

    response = client_for(user).put(url(product), {"score": 5}, format="json")

    assert response.status_code == 403


def test_delivered_order_of_another_product_does_not_count(buyer, product):
    other = Product.objects.create(
        name="Brazil", model="BRA", serial_number="SN-BRA", description="t",
        quantity_in_stock=5, price=Decimal("100.00"), distributor_name="D",
        category=product.category,
    )

    response = client_for(buyer).put(url(other), {"score": 5}, format="json")

    assert response.status_code == 403


def test_guest_cannot_rate(product):
    assert APIClient().put(url(product), {"score": 5}, format="json").status_code == 401


def test_staff_cannot_rate(product):
    manager = User.objects.create_user(
        email="pm@reviews.test", password="x", role=User.Role.PRODUCT_MANAGER
    )
    assert client_for(manager).put(url(product), {"score": 5}, format="json").status_code == 403


# --- Score rules ----------------------------------------------------------------


@pytest.mark.parametrize("score", [0, 6, -1, "abc", None])
def test_score_must_be_1_to_5(buyer, product, score):
    response = client_for(buyer).put(url(product), {"score": score}, format="json")

    assert response.status_code == 400
    assert not Rating.objects.exists()


def test_rating_again_changes_the_score_instead_of_adding(buyer, product):
    client = client_for(buyer)
    client.put(url(product), {"score": 2}, format="json")

    response = client.put(url(product), {"score": 5}, format="json")

    assert response.status_code == 200
    assert Rating.objects.filter(user=buyer, product=product).count() == 1
    assert Rating.objects.get(user=buyer, product=product).score == 5


def test_unknown_product_is_404(buyer):
    response = client_for(buyer).put("/api/products/999999/my-rating/", {"score": 3}, format="json")
    assert response.status_code == 404


# --- GET my rating (for the product page) ---------------------------------------


def test_get_my_rating_before_and_after_rating(buyer, product):
    client = client_for(buyer)
    assert client.get(url(product)).data == {"score": None, "can_rate": True}

    client.put(url(product), {"score": 3}, format="json")

    assert client.get(url(product)).data == {"score": 3, "can_rate": True}


def test_get_my_rating_tells_non_buyer_they_cannot_rate(product):
    user = make_customer("stranger2@reviews.test")
    assert client_for(user).get(url(product)).data == {"score": None, "can_rate": False}


# --- Average on the product -----------------------------------------------------


def test_product_without_ratings_has_null_average(product):
    data = APIClient().get(f"/api/products/{product.id}/").data

    assert data["average_rating"] is None
    assert data["rating_count"] == 0


def test_average_and_count_on_product_detail_and_list(product):
    for i, score in enumerate([5, 4, 4]):
        user = make_customer(f"r{i}@reviews.test")
        buy(user, product)
        client_for(user).put(url(product), {"score": score}, format="json")

    detail = APIClient().get(f"/api/products/{product.id}/").data
    listed = APIClient().get("/api/products/").data["results"][0]

    assert detail["average_rating"] == 4.3  # 13 / 3 = 4.33, rounded to 1 decimal
    assert detail["rating_count"] == 3
    assert listed["average_rating"] == 4.3
    assert listed["rating_count"] == 3


def test_buying_the_product_twice_still_counts_one_rating(buyer, product):
    buy(buyer, product)  # second delivered order of the same product
    client_for(buyer).put(url(product), {"score": 5}, format="json")

    data = APIClient().get(f"/api/products/{product.id}/").data

    assert data["rating_count"] == 1