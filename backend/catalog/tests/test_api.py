from decimal import Decimal

from rest_framework.test import APITestCase

from catalog.models import Category, Product


class CatalogApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.beans = Category.objects.create(name="Coffee Beans")
        cls.grinders = Category.objects.create(name="Grinders")

        def product(name, model, price, stock, category, description="", popularity=0):
            return Product.objects.create(
                name=name, model=model, serial_number=f"SN-{model}",
                description=description or name, quantity_in_stock=stock,
                price=Decimal(price), cost=Decimal("1.00"),
                distributor_name="D", category=category, popularity=popularity,
            )

        cls.kenya = product("Kenya AA", "KEN", "590", 0, cls.beans,
                            description="Notes of blackcurrant and grapefruit", popularity=5)
        cls.brazil = product("Brazil Cerrado", "BRA", "1350", 30, cls.beans, popularity=20)
        cls.grinder = product("Manual Grinder", "GRD", "2450", 18, cls.grinders, popularity=10)

    def get_names(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return [p["name"] for p in response.json()["results"]]

    # --- KAN-24: list / detail / categories --------------------------------

    def test_list_is_public_and_paginated(self):
        response = self.client.get("/api/products/")  # no login (Req 4)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 3)
        self.assertIn("next", body)

    def test_detail_returns_req9_fields_but_not_cost(self):
        response = self.client.get(f"/api/products/{self.kenya.id}/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for field in ["id", "name", "model", "serial_number", "description",
                      "quantity_in_stock", "price", "warranty_status",
                      "distributor_name", "in_stock"]:
            self.assertIn(field, body)
        self.assertNotIn("cost", body)  # internal data (Req 17)
        self.assertEqual(body["category"]["name"], "Coffee Beans")

    def test_unknown_product_returns_404(self):
        self.assertEqual(self.client.get("/api/products/999999/").status_code, 404)

    def test_filter_by_category(self):
        names = self.get_names(f"/api/products/?category={self.grinders.id}")
        self.assertEqual(names, ["Manual Grinder"])

    def test_invalid_category_returns_400(self):
        self.assertEqual(self.client.get("/api/products/?category=abc").status_code, 400)

    def test_categories_endpoint_lists_all(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_products_are_read_only(self):
        response = self.client.post("/api/products/", {"name": "Hack"})
        self.assertEqual(response.status_code, 405)

    # --- KAN-25: search & sort (Req 7) -------------------------------------

    def test_search_matches_description_case_insensitive(self):
        self.assertEqual(self.get_names("/api/products/?search=BLACKCURRANT"), ["Kenya AA"])

    def test_out_of_stock_product_still_appears_in_search(self):
        response = self.client.get("/api/products/?search=kenya")
        result = response.json()["results"][0]
        self.assertEqual(result["name"], "Kenya AA")
        self.assertFalse(result["in_stock"])

    def test_sort_by_price_both_directions(self):
        self.assertEqual(self.get_names("/api/products/?ordering=price"),
                         ["Kenya AA", "Brazil Cerrado", "Manual Grinder"])
        self.assertEqual(self.get_names("/api/products/?ordering=-price"),
                         ["Manual Grinder", "Brazil Cerrado", "Kenya AA"])

    def test_sort_by_popularity_most_popular_first(self):
        self.assertEqual(self.get_names("/api/products/?ordering=-popularity"),
                         ["Brazil Cerrado", "Manual Grinder", "Kenya AA"])

    def test_cannot_sort_by_hidden_cost_field(self):
        # unknown ordering field is ignored -> default ordering by name
        self.assertEqual(self.get_names("/api/products/?ordering=cost"),
                         ["Brazil Cerrado", "Kenya AA", "Manual Grinder"])
