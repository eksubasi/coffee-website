from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.models import Category, Product


def run_seed():
    out = StringIO()
    call_command("seed_catalog", stdout=out)
    return out.getvalue()


class SeedCatalogTests(TestCase):
    """Uses the real catalog/data/Brewnook_Product_List.xlsx."""

    def test_seed_loads_all_products_and_categories(self):
        run_seed()
        self.assertEqual(Category.objects.count(), 7)
        self.assertEqual(Product.objects.count(), 32)

    def test_seed_is_idempotent(self):
        run_seed()
        output = run_seed()
        self.assertEqual(Product.objects.count(), 32)
        self.assertIn("0 products created, 32 updated", output)

    def test_seed_keeps_test_fixtures_and_blank_cost(self):
        run_seed()
        self.assertEqual(Product.objects.get(model="DB-KEN-250").quantity_in_stock, 0)
        self.assertEqual(Product.objects.get(model="BW-E64").quantity_in_stock, 0)
        self.assertEqual(Product.objects.get(model="DB-GUA-250").quantity_in_stock, 1)
        colombia = Product.objects.get(model="DB-COL-250")
        self.assertIsNone(colombia.cost)
        self.assertEqual(colombia.effective_cost, Decimal("230.00"))

    def test_reseed_does_not_reset_popularity(self):
        run_seed()
        Product.objects.filter(model="BW-M1").update(popularity=50)
        run_seed()
        self.assertEqual(Product.objects.get(model="BW-M1").popularity, 50)

    def test_missing_file_gives_clear_error(self):
        with self.assertRaisesMessage(CommandError, "File not found"):
            call_command("seed_catalog", file=Path("does-not-exist.xlsx"), stdout=StringIO())
