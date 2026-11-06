from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from catalog.models import Category, Product


def make_product(category, **overrides):
    data = {
        "name": "Test Grinder",
        "model": "T-1",
        "serial_number": "SN-T-1",
        "description": "A test product",
        "quantity_in_stock": 5,
        "price": Decimal("100.00"),
        "distributor_name": "Test Distributor",
        "category": category,
    }
    data.update(overrides)
    return Product.objects.create(**data)


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Grinders")

    def test_cost_defaults_to_half_of_price_when_empty(self):
        """Req 11: blank cost -> 50% of the sale price."""
        product = make_product(self.category, price=Decimal("460.00"), cost=None)
        self.assertEqual(product.effective_cost, Decimal("230.00"))

    def test_given_cost_is_used_as_is(self):
        product = make_product(self.category, price=Decimal("520.00"), cost=Decimal("260.00"))
        self.assertEqual(product.effective_cost, Decimal("260.00"))

    def test_in_stock_depends_on_quantity(self):
        self.assertFalse(make_product(self.category, model="T-0", quantity_in_stock=0).in_stock)
        self.assertTrue(make_product(self.category, model="T-5", quantity_in_stock=5).in_stock)

    def test_negative_price_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_product(self.category, price=Decimal("-1.00"))

    def test_negative_stock_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_product(self.category, quantity_in_stock=-1)

    def test_model_code_must_be_unique(self):
        make_product(self.category, model="DUP-1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_product(self.category, model="DUP-1")

    def test_category_with_products_cannot_be_deleted(self):
        make_product(self.category)
        with self.assertRaises(ProtectedError):
            self.category.delete()
