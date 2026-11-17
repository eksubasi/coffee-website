"""KAN-57: comments need a delivered purchase and product-manager approval."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order, OrderItem
from reviews.models import Comment


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


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def buy(user, product, status=Order.Status.DELIVERED):
    order = Order.objects.create(user=user, address="1 Coffee Street", status=status)
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price=product.price)


@pytest.fixture
def buyer(product):
    user = User.objects.create_user(
        email="buyer@comments.test", password="x", full_name="Melike Yildirim"
    )
    buy(user, product)
    return user


@pytest.fixture
def manager(db):
    return User.objects.create_user(
        email="pm@comments.test", password="x", role=User.Role.PRODUCT_MANAGER
    )


def comments_url(product):
    return f"/api/products/{product.id}/comments/"


def post_comment(user, product, text="Great beans, fruity and bright."):
    return client_for(user).post(comments_url(product), {"text": text}, format="json")


# --- Posting ---------------------------------------------------------------------


def test_buyer_can_comment_and_it_starts_pending(buyer, product):
    response = post_comment(buyer, product)

    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert Comment.objects.get().status == Comment.Status.PENDING


@pytest.mark.parametrize(
    "status", [Order.Status.PROCESSING, Order.Status.IN_TRANSIT, Order.Status.CANCELLED]
)
def test_order_not_delivered_cannot_comment(product, status):
    user = User.objects.create_user(email="waiting@comments.test", password="x")
    buy(user, product, status=status)

    assert post_comment(user, product).status_code == 403
    assert not Comment.objects.exists()


def test_customer_who_never_bought_cannot_comment(product):
    user = User.objects.create_user(email="stranger@comments.test", password="x")
    assert post_comment(user, product).status_code == 403


def test_guest_cannot_comment(product):
    response = APIClient().post(comments_url(product), {"text": "hi"}, format="json")
    assert response.status_code == 401


def test_manager_cannot_post_comments(manager, product):
    assert post_comment(manager, product).status_code == 403


@pytest.mark.parametrize("text", ["", "   ", "x" * 1001])
def test_comment_text_must_be_1_to_1000_characters(buyer, product, text):
    assert post_comment(buyer, product, text=text).status_code == 400


def test_unknown_product_is_404(buyer):
    response = client_for(buyer).post("/api/products/999999/comments/", {"text": "hi"}, format="json")
    assert response.status_code == 404


# --- Public list -----------------------------------------------------------------


def test_pending_and_rejected_comments_are_hidden_from_visitors(buyer, product):
    Comment.objects.create(user=buyer, product=product, text="pending one")
    Comment.objects.create(
        user=buyer, product=product, text="rejected one", status=Comment.Status.REJECTED
    )

    response = APIClient().get(comments_url(product))

    assert response.status_code == 200
    assert response.data["results"] == []


def test_approved_comment_is_public_without_the_email(buyer, product):
    Comment.objects.create(
        user=buyer, product=product, text="Lovely", status=Comment.Status.APPROVED
    )

    results = APIClient().get(comments_url(product)).data["results"]

    assert len(results) == 1
    assert results[0]["text"] == "Lovely"
    assert results[0]["author"] == "Melike Y."
    assert "buyer@comments.test" not in str(results[0])


def test_comments_of_other_products_are_not_listed(buyer, product):
    other = Product.objects.create(
        name="Brazil", model="BRA", serial_number="SN-BRA", description="t",
        quantity_in_stock=5, price=Decimal("100.00"), distributor_name="D",
        category=product.category,
    )
    Comment.objects.create(user=buyer, product=other, text="x", status=Comment.Status.APPROVED)

    assert APIClient().get(comments_url(product)).data["results"] == []


# --- My comments (pending notice) ------------------------------------------------


def test_customer_sees_own_pending_comment(buyer, product):
    post_comment(buyer, product, text="waiting for approval")
    someone = User.objects.create_user(email="other@comments.test", password="x")
    Comment.objects.create(user=someone, product=product, text="not mine")

    data = client_for(buyer).get(f"/api/products/{product.id}/comments/mine/").data

    assert [(c["text"], c["status"]) for c in data] == [("waiting for approval", "pending")]


# --- Moderation (product manager) ------------------------------------------------


def test_manager_sees_pending_queue(buyer, manager, product):
    post_comment(buyer, product, text="first")
    Comment.objects.create(user=buyer, product=product, text="done", status=Comment.Status.APPROVED)

    data = client_for(manager).get("/api/comments/?status=pending").data["results"]

    assert [c["text"] for c in data] == ["first"]
    assert data[0]["product_name"] == "Kenya AA"
    assert data[0]["customer_email"] == "buyer@comments.test"


def test_bad_status_filter_is_400(manager):
    assert client_for(manager).get("/api/comments/?status=maybe").status_code == 400


def test_approve_makes_comment_public(buyer, manager, product):
    comment_id = post_comment(buyer, product).data["id"]

    response = client_for(manager).patch(f"/api/comments/{comment_id}/approve/")

    assert response.status_code == 200
    assert response.data["status"] == "approved"
    assert response.data["reviewed_by_email"] == "pm@comments.test"
    assert response.data["reviewed_at"] is not None
    assert len(APIClient().get(comments_url(product)).data["results"]) == 1


def test_reject_keeps_comment_hidden(buyer, manager, product):
    comment_id = post_comment(buyer, product).data["id"]

    response = client_for(manager).patch(f"/api/comments/{comment_id}/reject/")

    assert response.data["status"] == "rejected"
    assert APIClient().get(comments_url(product)).data["results"] == []
    mine = client_for(buyer).get(f"/api/products/{product.id}/comments/mine/").data
    assert mine[0]["status"] == "rejected"


def test_manager_can_change_their_mind(buyer, manager, product):
    comment_id = post_comment(buyer, product).data["id"]
    pm = client_for(manager)
    pm.patch(f"/api/comments/{comment_id}/reject/")

    response = pm.patch(f"/api/comments/{comment_id}/approve/")

    assert response.data["status"] == "approved"


@pytest.mark.parametrize("action", ["approve", "reject"])
def test_customer_cannot_moderate(buyer, product, action):
    comment_id = post_comment(buyer, product).data["id"]

    response = client_for(buyer).patch(f"/api/comments/{comment_id}/{action}/")

    assert response.status_code == 403
    assert Comment.objects.get(pk=comment_id).status == Comment.Status.PENDING


def test_customer_cannot_see_moderation_queue(buyer):
    assert client_for(buyer).get("/api/comments/").status_code == 403


def test_approving_unknown_comment_is_404(manager):
    assert client_for(manager).patch("/api/comments/999999/approve/").status_code == 404