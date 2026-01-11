######################################################################
# Product API Service Test Suite
######################################################################
import os
import logging
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus

from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/products"


class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        db.session.close()

    def setUp(self):
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    # ----------------------------------------------------------
    # Utility
    # ----------------------------------------------------------
    def _create_products(self, count=1):
        products = []
        for _ in range(count):
            product = ProductFactory()
            resp = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            data = resp.get_json()
            product.id = data["id"]
            products.append(product)
        return products

    # ----------------------------------------------------------
    # READ
    # ----------------------------------------------------------
    def test_get_product(self):
        product = self._create_products(1)[0]
        resp = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["name"], product.name)

    def test_get_product_not_found(self):
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # UPDATE
    # ----------------------------------------------------------
    def test_update_product(self):
        product = ProductFactory()
        resp = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        new_product = resp.get_json()
        new_product["description"] = "unknown"

        resp = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["description"], "unknown")

    # ----------------------------------------------------------
    # DELETE
    # ----------------------------------------------------------
    def test_delete_product(self):
        product = self._create_products(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{product.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ----------------------------------------------------------
    # LIST ALL
    # ----------------------------------------------------------
    def test_list_all_products(self):
        self._create_products(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.get_json()), 5)

    # ----------------------------------------------------------
    # LIST BY NAME
    # ----------------------------------------------------------
    def test_list_by_name(self):
        products = self._create_products(5)
        name = quote_plus(products[0].name)
        resp = self.client.get(f"{BASE_URL}?name={name}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for product in resp.get_json():
            self.assertEqual(product["name"], products[0].name)

    # ----------------------------------------------------------
    # LIST BY CATEGORY
    # ----------------------------------------------------------
    def test_list_by_category(self):
        products = self._create_products(5)
        category = products[0].category.name
        resp = self.client.get(f"{BASE_URL}?category={category}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for product in resp.get_json():
            self.assertEqual(product["category"], category)

    # ----------------------------------------------------------
    # LIST BY AVAILABILITY
    # ----------------------------------------------------------
    def test_list_by_availability(self):
        products = self._create_products(10)
        available = str(products[0].available)
        resp = self.client.get(f"{BASE_URL}?available={available}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for product in resp.get_json():
            self.assertEqual(str(product["available"]), available)
