"""
KAN-23: python manage.py seed_catalog [--file path/to/Brewnook_Product_List.xlsx]

Reads the "Categories" and "Products" sheets and loads them into the database.
Idempotent: products are matched by their model code (update_or_create),
so running the command twice does not create duplicates.
Popularity is never touched, so re-seeding does not reset real usage data.
"""
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from catalog.models import Category, Product

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "data" / "Brewnook_Product_List.xlsx"

# Excel column header -> Product field
PRODUCT_COLUMNS = {
    "Name": "name",
    "Brand": "brand",
    "Serial / Lot No": "serial_number",
    "Description": "description",
    "Quantity in Stock": "quantity_in_stock",
    "Price (TRY)": "price",
    # Only the optional cost column is used; "Calculated Cost" is an Excel
    # formula and the 50% default is handled by Product.effective_cost.
    "Cost (TRY, optional)": "cost",
    "Warranty Status": "warranty_status",
    "Warranty (months)": "warranty_months",
    "Distributor": "distributor_name",
    "Distributor Contact": "distributor_contact",
    "Expiry Date": "expiry_date",
    "Roast Date": "roast_date",
    "Origin": "origin",
    "Weight / Capacity": "weight_capacity",
    "Image File": "image",
}
DECIMAL_FIELDS = {"price", "cost"}
INT_FIELDS = {"quantity_in_stock", "warranty_months"}
DATE_FIELDS = {"expiry_date", "roast_date"}
REQUIRED_HEADERS = set(PRODUCT_COLUMNS) | {"Model", "Category"}


def _rows_as_dicts(sheet):
    rows = sheet.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else None for h in next(rows)]
    for row in rows:
        yield dict(zip(headers, row))


def _convert(field, value):
    if value is None or value == "":
        if field in DECIMAL_FIELDS | DATE_FIELDS:
            return None
        if field in INT_FIELDS:
            return 0
        return ""
    if field in DECIMAL_FIELDS:
        return Decimal(str(value))
    if field in INT_FIELDS:
        return int(value)
    if field in DATE_FIELDS:
        # Excel cells may hold real dates or ISO text like "2027-10-05"
        return value.date() if hasattr(value, "date") else date.fromisoformat(str(value))
    return str(value).strip()


class Command(BaseCommand):
    help = "Load categories and products from the Brewnook product list (.xlsx)."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=DEFAULT_FILE)

    @transaction.atomic  # all-or-nothing: a bad row leaves the DB unchanged
    def handle(self, *args, **options):
        path = options["file"]
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        workbook = load_workbook(path, data_only=True, read_only=True)

        categories = {}
        for row in _rows_as_dicts(workbook["Categories"]):
            name = row.get("Category")
            if not name or not row.get("Description"):  # skips the "Total" row
                continue
            category, _ = Category.objects.update_or_create(
                name=name.strip(), defaults={"description": row["Description"].strip()}
            )
            categories[category.name] = category

        created = updated = 0
        product_rows = list(_rows_as_dicts(workbook["Products"]))
        missing = REQUIRED_HEADERS - set(product_rows[0]) if product_rows else REQUIRED_HEADERS
        if missing:
            raise CommandError(f"Products sheet is missing columns: {sorted(missing)}")

        for row in product_rows:
            model_code = row.get("Model")
            if not model_code:
                continue
            category_name = (row.get("Category") or "").strip()
            if category_name not in categories:
                raise CommandError(f"{model_code}: unknown category '{category_name}'")

            fields = {f: _convert(f, row.get(col)) for col, f in PRODUCT_COLUMNS.items()}
            fields["category"] = categories[category_name]
            _, was_created = Product.objects.update_or_create(
                model=str(model_code).strip(), defaults=fields
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(
            f"{len(categories)} categories, {created} products created, {updated} updated."
        ))
