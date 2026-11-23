"""KAN-62: customer wishlist API."""

from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product
from wishlist.models import WishlistItem


@pytest.fixture
def products(db):
    category = Category.objects.create(name="Wishlist Test")

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
            image=f"products/{model.lower()}.webp",
        )

    return {"beans": make("W1", "100.00", 10), "kenya": make("W2", "80.00", 0)}


def make_user(email, role=User.Role.CUSTOMER):
    return User.objects.create_user(email=email, password="x", role=role)


@pytest.fixture
def customer(db):
    return make_user("wish@test.com")


@pytest.fixture
def api(customer):
    client = APIClient()
    client.force_authenticate(customer)
    return client


def add(api, product_id):
    return api.post(reverse("wishlist"), {"product_id": product_id}, format="json")


def item_url(product_id):
    return reverse("wishlist-item", args=[product_id])


@pytest.mark.django_db
def test_add_product_returns_201_with_summary(api, customer, products):
    response = add(api, products["beans"].id)

    assert response.status_code == 201
    body = response.json()
    assert body["product"] == {
        "id": products["beans"].id,
        "name": "Product W1",
        "model": "W1",
        "price": "100.00",
        "image": "products/w1.webp",
        "in_stock": True,
    }
    assert "created_at" in body
    assert WishlistItem.objects.filter(user=customer, product=products["beans"]).exists()


@pytest.mark.django_db
def test_add_duplicate_is_idempotent(api, customer, products):
    first = add(api, products["beans"].id)
    second = add(api, products["beans"].id)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert WishlistItem.objects.filter(user=customer).count() == 1


@pytest.mark.django_db
def test_list_returns_own_items_newest_first(api, products):
    add(api, products["beans"].id)
    add(api, products["kenya"].id)

    response = api.get(reverse("wishlist"))

    assert response.status_code == 200
    body = response.json()
    assert [entry["product"]["id"] for entry in body] == [
        products["kenya"].id,
        products["beans"].id,
    ]
    assert body[0]["product"]["in_stock"] is False


@pytest.mark.django_db
def test_remove_item(api, customer, products):
    add(api, products["beans"].id)

    response = api.delete(item_url(products["beans"].id))

    assert response.status_code == 204
    assert not WishlistItem.objects.filter(user=customer).exists()
    # Removing again: nothing left to delete.
    assert api.delete(item_url(products["beans"].id)).status_code == 404


@pytest.mark.django_db
def test_cannot_see_or_remove_other_customers_items(api, customer, products):
    other = make_user("other@test.com")
    WishlistItem.objects.create(user=other, product=products["kenya"])

    listed = api.get(reverse("wishlist"))
    removed = api.delete(item_url(products["kenya"].id))

    assert listed.status_code == 200
    assert listed.json() == []
    assert removed.status_code == 404
    assert WishlistItem.objects.filter(user=other).count() == 1


@pytest.mark.django_db
def test_same_product_in_two_wishlists(api, customer, products):
    other = make_user("other@test.com")
    WishlistItem.objects.create(user=other, product=products["beans"])

    assert add(api, products["beans"].id).status_code == 201
    assert WishlistItem.objects.filter(product=products["beans"]).count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [{}, {"product_id": 999999}, {"product_id": "abc"}])
def test_add_invalid_product_returns_400(api, products, payload):
    response = api.post(reverse("wishlist"), payload, format="json")

    assert response.status_code == 400
    assert "product_id" in response.json()
    assert not WishlistItem.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role",
    [User.Role.SALES_MANAGER, User.Role.PRODUCT_MANAGER, User.Role.SUPPORT_AGENT],
)
def test_non_customer_roles_get_403(products, role):
    client = APIClient()
    client.force_authenticate(make_user(f"{role}@test.com", role=role))

    assert client.get(reverse("wishlist")).status_code == 403
    assert add(client, products["beans"].id).status_code == 403
    assert client.delete(item_url(products["beans"].id)).status_code == 403
    assert not WishlistItem.objects.exists()


@pytest.mark.django_db
def test_anonymous_gets_401(products):
    client = APIClient()

    assert client.get(reverse("wishlist")).status_code == 401
    assert add(client, products["beans"].id).status_code == 401
    assert client.delete(item_url(products["beans"].id)).status_code == 401


@pytest.mark.django_db
def test_unique_constraint_on_user_and_product(customer, products):
    WishlistItem.objects.create(user=customer, product=products["beans"])

    with pytest.raises(IntegrityError):
        WishlistItem.objects.create(user=customer, product=products["beans"])


@pytest.mark.django_db
def test_deleting_product_removes_wishlist_items(customer, products):
    WishlistItem.objects.create(user=customer, product=products["beans"])

    products["beans"].delete()

    assert not WishlistItem.objects.exists()
