"""
KAN-24: serializers turn Product/Category objects into JSON for the API.

KAN-50 / KAN-59: the Manage* serializers at the bottom are used only by the
product-manager API (catalog/manage_views.py).
"""
from decimal import Decimal

from rest_framework import serializers

from catalog.models import Category, Product

# Upper limit for stock values. Keeps a typo like 10000000000 from crashing
# the database (the column is a 32-bit integer) and returns a clear 400 instead.
MAX_STOCK = 100_000


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class CategoryBriefSerializer(serializers.ModelSerializer):
    """Small version nested inside each product (no description needed there)."""

    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategoryBriefSerializer(read_only=True)
    # Computed in the model (Req 7): frontend disables "Add to cart" when False
    in_stock = serializers.BooleanField(read_only=True)
    # KAN-56 (Req 5): filled in by ProductViewSet.get_queryset with one SQL query.
    # average_rating is null when nobody has rated the product yet.
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # Public fields only. "cost" is internal business data (used for
        # profit/loss, Req 11) so it is NOT exposed to customers.
        fields = [
            "id", "name", "model", "serial_number", "description",
            "quantity_in_stock", "in_stock", "price",
            "warranty_status", "warranty_months",
            "distributor_name", "distributor_contact",
            "category", "image",
            "brand", "origin", "roast_date", "expiry_date", "weight_capacity",
            "popularity", "average_rating", "rating_count",
        ]
        read_only_fields = fields

    def get_average_rating(self, product):
        average = getattr(product, "average_rating", None)
        return round(average, 1) if average is not None else None

    def get_rating_count(self, product):
        return getattr(product, "rating_count", 0)


# --- KAN-50: product manager, products ---------------------------------------


class ManageProductSerializer(serializers.ModelSerializer):
    """
    Add / edit form of the product manager (Req 9 fields + optional cost).

    Two fields can be given only when the product is ADDED:
    - price: after that, prices belong to the sales manager (Req 11, KAN-76).
    - quantity_in_stock: after that, stock changes go through
      PATCH /api/manage/products/{id}/stock, which locks the row (KAN-59).
    When editing, these two are read-only: values sent for them are ignored.
    """

    # Written as an id ({"category": 3}), shown back with its name as well.
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_name = serializers.CharField(source="category.name", read_only=True)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    # Empty cost -> 50% of price is used for profit/loss (Req 11).
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0"),
        required=False, allow_null=True,
    )
    quantity_in_stock = serializers.IntegerField(
        min_value=0, max_value=MAX_STOCK, required=False  # model default: 0
    )
    in_stock = serializers.BooleanField(read_only=True)
    effective_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id", "name", "model", "serial_number", "description",
            "quantity_in_stock", "in_stock", "price", "cost", "effective_cost",
            "warranty_status", "warranty_months",
            "distributor_name", "distributor_contact",
            "category", "category_name", "image",
            "brand", "origin", "roast_date", "expiry_date", "weight_capacity",
            "popularity", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "popularity", "created_at", "updated_at"]

    CREATE_ONLY_FIELDS = ("price", "quantity_in_stock")

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is not None:  # editing an existing product
            for name in self.CREATE_ONLY_FIELDS:
                fields[name].read_only = True
        return fields

    def validate(self, attrs):
        # On a partial edit (PATCH) a field may be missing from attrs, so fall
        # back to the value the product already has.
        def value(name):
            return attrs.get(name, getattr(self.instance, name, None))

        warranty_status = value("warranty_status") or Product.WarrantyStatus.NO_WARRANTY
        warranty_months = value("warranty_months") or 0
        if warranty_status == Product.WarrantyStatus.UNDER_WARRANTY and warranty_months == 0:
            raise serializers.ValidationError(
                {"warranty_months": "A product under warranty needs warranty_months > 0."}
            )
        if warranty_status == Product.WarrantyStatus.NO_WARRANTY and warranty_months > 0:
            raise serializers.ValidationError(
                {"warranty_months": "Set warranty_months to 0 for a product with no warranty."}
            )

        roast_date, expiry_date = value("roast_date"), value("expiry_date")
        if roast_date and expiry_date and expiry_date <= roast_date:
            raise serializers.ValidationError(
                {"expiry_date": "Expiry date must be after the roast date."}
            )
        return attrs

    def update(self, instance, validated_data):
        for name, new_value in validated_data.items():
            setattr(instance, name, new_value)
        # Save only the fields that were sent. A plain save() writes every
        # column, so it could put back an old stock or popularity value that
        # a checkout changed a moment ago (Req 18: lost update).
        instance.save(update_fields=[*validated_data, "updated_at"])
        return instance


class StockUpdateSerializer(serializers.Serializer):
    """
    KAN-59: body of PATCH /api/manage/products/{id}/stock. Send exactly one:
    {"quantity_in_stock": 40}  set the stock to 40
    {"change": -3}             remove 3 (the +/- buttons)
    """

    quantity_in_stock = serializers.IntegerField(
        required=False, min_value=0, max_value=MAX_STOCK
    )
    change = serializers.IntegerField(
        required=False, min_value=-MAX_STOCK, max_value=MAX_STOCK
    )

    def validate(self, attrs):
        if len(attrs) != 1:
            raise serializers.ValidationError(
                "Send exactly one of 'quantity_in_stock' (set) or 'change' (+/-)."
            )
        if attrs.get("change") == 0:
            raise serializers.ValidationError({"change": "Must not be 0."})
        return attrs


# --- KAN-59: product manager, categories -------------------------------------


class ManageCategorySerializer(serializers.ModelSerializer):
    # Shown in the table so the manager can see which categories can be deleted.
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "description", "product_count"]

    def get_product_count(self, category):
        # Filled in by the viewset's annotate(); counted directly after a create.
        count = getattr(category, "product_count", None)
        return count if count is not None else category.products.count()

    def validate_name(self, name):
        # The database only blocks exact duplicates; also block "coffee beans"
        # when "Coffee Beans" already exists.
        duplicates = Category.objects.filter(name__iexact=name)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return name