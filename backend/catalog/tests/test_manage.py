"""
KAN-50 + KAN-59: product-manager API for products, categories and stock.
"""
import threading
from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product
from catalog.serializers import ManageProductSerializer
from orders.models import Order, OrderItem

PRODUCTS = "/api/manage/products"
CATEGORIES = "/api/manage/categories"


# --- Fixtures ----------------------------------------------------------------


def client_for(role):
    user = User.objects.create_user(email=f"{role}@manage.test", password="x", role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def pm(db):
    return client_for(User.Role.PRODUCT_MANAGER)


@pytest.fixture
def beans(db):
    return Category.objects.create(name="Coffee Beans")


@pytest.fixture
def grinders(db):
    return Category.objects.create(name="Grinders")


@pytest.fixture
def kenya(beans):
    return Product.objects.create(
        name="Kenya AA", model="KEN-AA", serial_number="LOT-KEN",
        description="Blackcurrant", quantity_in_stock=10, price=Decimal("590.00"),
        distributor_name="Bean Co", category=beans,
    )


def new_product_body(in_category, **changes):
    body = {
        "name": "Ethiopia Yirgacheffe",
        "model": "ETH-YIR",
        "serial_number": "LOT-ETH",
        "description": "Floral and citrus",
        "quantity_in_stock": 25,
        "price": "640.00",
        "cost": "300.00",
        "warranty_status": "No warranty",
        "warranty_months": 0,
        "distributor_name": "Bean Co",
        "category": in_category.id,
    }
    body.update(changes)
    return body


# --- Permissions (Req 10, 17: roles are not mixed) ---------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("role", [
    User.Role.CUSTOMER, User.Role.SALES_MANAGER, User.Role.SUPPORT_AGENT,
])
def test_other_roles_get_403(role, kenya):
    client = client_for(role)
    assert client.get(PRODUCTS).status_code == 403
    assert client.get(CATEGORIES).status_code == 403
    assert client.post(PRODUCTS, {}, format="json").status_code == 403
    response = client.patch(f"{PRODUCTS}/{kenya.id}/stock", {"change": 5}, format="json")
    assert response.status_code == 403
    kenya.refresh_from_db()
    assert kenya.quantity_in_stock == 10


@pytest.mark.django_db
def test_anonymous_gets_401():
    assert APIClient().get(PRODUCTS).status_code == 401
    assert APIClient().get(CATEGORIES).status_code == 401


# --- KAN-50: list / add / edit / delete --------------------------------------


def test_list_shows_cost_to_product_manager(pm, kenya):
    response = pm.get(PRODUCTS)

    assert response.status_code == 200
    [row] = response.json()  # not paginated: the manager table needs every row
    assert row["cost"] is None
    assert row["effective_cost"] == "295.00"  # Req 11: empty cost -> 50% of price
    assert row["category"] == kenya.category_id
    assert row["category_name"] == "Coffee Beans"


def test_added_product_appears_in_storefront(pm, beans):
    response = pm.post(PRODUCTS, new_product_body(beans), format="json")

    assert response.status_code == 201
    product_id = response.json()["id"]
    public = APIClient().get(f"/api/products/{product_id}/")
    assert public.status_code == 200
    assert public.json()["quantity_in_stock"] == 25
    assert "cost" not in public.json()  # still hidden from customers


def test_add_without_cost_and_stock_uses_defaults(pm, beans):
    body = new_product_body(beans)
    del body["cost"], body["quantity_in_stock"]

    response = pm.post(PRODUCTS, body, format="json")

    assert response.status_code == 201
    assert response.json()["effective_cost"] == "320.00"
    assert response.json()["quantity_in_stock"] == 0
    assert response.json()["in_stock"] is False


@pytest.mark.parametrize("changes,bad_field", [
    ({"price": "-5.00"}, "price"),
    ({"price": "0"}, "price"),
    ({"cost": "-1"}, "cost"),
    ({"quantity_in_stock": -1}, "quantity_in_stock"),
    ({"category": 99999}, "category"),
    ({"warranty_status": "Under warranty", "warranty_months": 0}, "warranty_months"),
    ({"warranty_status": "No warranty", "warranty_months": 12}, "warranty_months"),
    ({"roast_date": "2026-11-01", "expiry_date": "2026-10-01"}, "expiry_date"),
    ({"name": ""}, "name"),
])
def test_add_rejects_invalid_data(pm, beans, changes, bad_field):
    response = pm.post(PRODUCTS, new_product_body(beans, **changes), format="json")

    assert response.status_code == 400
    assert bad_field in response.json()
    assert not Product.objects.exists()


def test_add_rejects_duplicate_model_code(pm, beans, kenya):
    response = pm.post(PRODUCTS, new_product_body(beans, model="KEN-AA"), format="json")

    assert response.status_code == 400
    assert "model" in response.json()


def test_edit_changes_fields_but_not_price_or_stock(pm, kenya, grinders):
    response = pm.patch(
        f"{PRODUCTS}/{kenya.id}",
        {"name": "Kenya AA Nyeri", "cost": "250.00", "category": grinders.id,
         "price": "1.00", "quantity_in_stock": 999},
        format="json",
    )

    assert response.status_code == 200
    kenya.refresh_from_db()
    assert kenya.name == "Kenya AA Nyeri"
    assert kenya.cost == Decimal("250.00")
    assert kenya.category == grinders
    assert kenya.price == Decimal("590.00")  # sales manager's job (KAN-76)
    assert kenya.quantity_in_stock == 10    # only via /stock


def test_edit_keeps_partial_update_rules(pm, kenya):
    # Kenya has no warranty; turning it on without months must fail.
    response = pm.patch(
        f"{PRODUCTS}/{kenya.id}", {"warranty_status": "Under warranty"}, format="json"
    )

    assert response.status_code == 400
    assert "warranty_months" in response.json()


def test_edit_does_not_undo_a_stock_change_made_meanwhile(kenya):
    # The manager opens the edit form (product loaded with stock 10) ...
    loaded = Product.objects.get(pk=kenya.pk)
    # ... meanwhile a checkout sells 7 ...
    Product.objects.filter(pk=kenya.pk).update(quantity_in_stock=3)
    # ... then the manager saves a new name.
    serializer = ManageProductSerializer(loaded, data={"name": "Renamed"}, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    kenya.refresh_from_db()
    assert kenya.name == "Renamed"
    assert kenya.quantity_in_stock == 3  # not put back to 10


def test_delete_product_without_orders(pm, kenya):
    response = pm.delete(f"{PRODUCTS}/{kenya.id}")

    assert response.status_code == 204
    assert not Product.objects.filter(pk=kenya.pk).exists()
    assert APIClient().get(f"/api/products/{kenya.id}/").status_code == 404


def test_delete_ordered_product_is_refused(pm, kenya):
    customer = User.objects.create_user(email="buyer@manage.test", password="x")
    order = Order.objects.create(user=customer, address="1 Coffee Street")
    OrderItem.objects.create(order=order, product=kenya, quantity=1, unit_price=kenya.price)

    response = pm.delete(f"{PRODUCTS}/{kenya.id}")

    assert response.status_code == 409
    assert "stock to 0" in response.json()["detail"]
    assert Product.objects.filter(pk=kenya.pk).exists()


def test_unknown_product_is_404(pm):
    assert pm.get(f"{PRODUCTS}/99999").status_code == 404
    assert pm.patch(f"{PRODUCTS}/99999/stock", {"change": 1}, format="json").status_code == 404


# --- KAN-59: stock -----------------------------------------------------------


def stock(pm, product, body):
    return pm.patch(f"{PRODUCTS}/{product.id}/stock", body, format="json")


def test_set_stock_to_a_number(pm, kenya):
    response = stock(pm, kenya, {"quantity_in_stock": 40})

    assert response.status_code == 200
    assert response.json()["quantity_in_stock"] == 40
    kenya.refresh_from_db()
    assert kenya.quantity_in_stock == 40


def test_plus_and_minus_buttons(pm, kenya):
    assert stock(pm, kenya, {"change": 5}).json()["quantity_in_stock"] == 15
    assert stock(pm, kenya, {"change": -3}).json()["quantity_in_stock"] == 12


def test_stock_cannot_go_below_zero(pm, kenya):
    response = stock(pm, kenya, {"change": -11})

    assert response.status_code == 400
    assert "Only 10 in stock" in response.json()["change"][0]
    kenya.refresh_from_db()
    assert kenya.quantity_in_stock == 10


@pytest.mark.parametrize("body", [
    {},
    {"quantity_in_stock": 5, "change": 1},
    {"change": 0},
    {"quantity_in_stock": -1},
    {"quantity_in_stock": 10_000_000},
])
def test_stock_rejects_bad_bodies(pm, kenya, body):
    assert stock(pm, kenya, body).status_code == 400
    kenya.refresh_from_db()
    assert kenya.quantity_in_stock == 10


def test_stock_change_shows_on_storefront_badge(pm, kenya):
    stock(pm, kenya, {"quantity_in_stock": 0})

    body = APIClient().get(f"/api/products/{kenya.id}/").json()
    assert body["quantity_in_stock"] == 0
    assert body["in_stock"] is False  # "Out of stock" badge, add to cart disabled


@pytest.mark.django_db(transaction=True)
def test_two_managers_removing_the_last_item_at_once():
    category = Category.objects.create(name="Race")
    product = Product.objects.create(
        name="Guatemala", model="RACE-1", serial_number="LOT-R", description="x",
        quantity_in_stock=1, price=Decimal("90.00"), distributor_name="D", category=category,
    )
    clients = [client_for(User.Role.PRODUCT_MANAGER)]
    second = User.objects.create_user(
        email="pm2@manage.test", password="x", role=User.Role.PRODUCT_MANAGER
    )
    clients.append(APIClient())
    clients[1].force_authenticate(user=second)

    start = threading.Barrier(2)
    codes = []

    def remove_one(client):
        try:
            start.wait()  # both requests start at the same moment
            codes.append(stock(client, product, {"change": -1}).status_code)
        finally:
            connection.close()  # each thread has its own database connection

    threads = [threading.Thread(target=remove_one, args=(c,)) for c in clients]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(codes) == [200, 400]
    product.refresh_from_db()
    assert product.quantity_in_stock == 0


# --- KAN-59: categories ------------------------------------------------------


def test_category_list_has_product_counts(pm, kenya, grinders):
    response = pm.get(CATEGORIES)

    assert response.status_code == 200
    counts = {c["name"]: c["product_count"] for c in response.json()}
    assert counts == {"Coffee Beans": 1, "Grinders": 0}


def test_add_category_appears_publicly(pm):
    response = pm.post(CATEGORIES, {"name": "Kettles", "description": "Gooseneck"}, format="json")

    assert response.status_code == 201
    assert response.json()["product_count"] == 0
    names = [c["name"] for c in APIClient().get("/api/categories/").json()]
    assert "Kettles" in names


def test_category_names_are_unique_ignoring_case(pm, beans):
    response = pm.post(CATEGORIES, {"name": "coffee beans"}, format="json")

    assert response.status_code == 400
    assert "name" in response.json()


def test_rename_category(pm, beans):
    response = pm.patch(f"{CATEGORIES}/{beans.id}", {"name": "Whole Beans"}, format="json")

    assert response.status_code == 200
    beans.refresh_from_db()
    assert beans.name == "Whole Beans"


def test_rename_to_same_name_with_other_case_is_allowed(pm, beans):
    response = pm.patch(f"{CATEGORIES}/{beans.id}", {"name": "COFFEE BEANS"}, format="json")

    assert response.status_code == 200


def test_delete_empty_category(pm, grinders):
    assert pm.delete(f"{CATEGORIES}/{grinders.id}").status_code == 204
    assert not Category.objects.filter(pk=grinders.pk).exists()


def test_delete_category_with_products_is_refused(pm, kenya, beans):
    response = pm.delete(f"{CATEGORIES}/{beans.id}")

    assert response.status_code == 409
    assert "1 product" in response.json()["detail"]
    assert Category.objects.filter(pk=beans.pk).exists()
    assert Product.objects.filter(pk=kenya.pk).exists()


def test_roast_and_expiry_dates_are_saved(pm, beans):
    body = new_product_body(beans, roast_date="2026-11-01", expiry_date="2027-11-01")

    response = pm.post(PRODUCTS, body, format="json")

    assert response.status_code == 201
    product = Product.objects.get(pk=response.json()["id"])
    assert product.roast_date == date(2026, 11, 1)