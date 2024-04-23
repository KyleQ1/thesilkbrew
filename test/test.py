import unittest
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class TestInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}
    
    def test_audit(self):
        response = requests.get('http://localhost:3000/inventory/audit', headers=self.header)
        self.assertEqual(response.status_code, 200)
    def test_plan(self):
        response = requests.post('http://localhost:3000/inventory/plan', headers=self.header)
        self.assertEqual(response.status_code, 200)

    def test_deliver_capacity_plan(self):
        response = requests.post('http://localhost:3000/inventory/deliver/1', headers=self.header, json=
                                 {"potion_capacity": 0, "ml_capacity": 0})
        self.assertEqual(response.status_code, 200)

class TestCarts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}

    # TODO: Not sure how to test yet
    def test_search(self):
        response = requests.get('http://localhost:3000/carts/search', headers=self.header, 
                                json={"customer_name": "John Doe", "potion_sku": "MINI_RED_POTION",
                                      "search_page": 1, "sort_col": "timestamp", "sort_order": "desc"})
        self.assertEqual(response.status_code, 200)

    def test_visits(self):
        response = requests.get('http://localhost:3000/carts/visits/1', headers=self.header, 
                                json={"customer_name": "John Doe", "character_class": "Warrior", "level": 1})
        self.assertEqual(response.status_code, 200)

    def test_create_cart(self):
        response = requests.post('http://localhost:3000/carts/', headers=self.header, 
                                 json={"customer_name": "John Doe", "character_class": "Warrior", "level": 1})
        self.assertEqual(response.status_code, 200)
    
    def test_set_item_quantity(self):
        response = requests.post('http://localhost:3000/carts/1/items/MINI_RED_POTION', headers=self.header, 
                                 json={"quantity": 1})
        self.assertEqual(response.status_code, 200)
    
    def test_checkout(self):
        response = requests.post('http://localhost:3000/carts/1/checkout', headers=self.header,
                                 json={"payment_method": "gold"})
        self.assertEqual(response.status_code, 200)

class TestCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}
     
    def test_get_catalog(self):
        response = requests.get('http://localhost:3000/catalog')
        self.assertEqual(response.status_code, 200)

class TestBottler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}

    def test_post_deliver(self):
        response = requests.post('http://localhost:3000/bottler/deliver/1', json=[
            {"potion_type": [100, 0, 0, 0], "quantity": 1}], headers=self.header)
        self.assertEqual(response.status_code, 200)
    
    def test_easy_bottle_plan(self):
        response = requests.post('http://localhost:3000/bottler/plan', headers=self.header)
        self.assertEqual(response.status_code, 200)
    
class TestBarrels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}

    def test_post_deliver(self):
        response = requests.post('http://localhost:3000/barrels/deliver/1', json=[
            {"sku": "MINI_RED_BARREL", "ml_per_barrel": 100, "potion_type": [1, 0, 0, 0],  
             "price": 0, "quantity": 1}], headers=self.header)
        self.assertEqual(response.status_code, 200)
    
    def test_get_wholesale_purchase_plan(self):
        response = requests.post('http://localhost:3000/barrels/plan', json=[
            {"sku": "MINI_RED_BARREL", "ml_per_barrel": 100, "potion_type": [1, 0, 0, 0],  
             "price": 0, "quantity": 1}], headers=self.header)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(loader.loadTestsFromTestCase(TestInventory))
    suite.addTest(loader.loadTestsFromTestCase(TestCarts))
    suite.addTest(loader.loadTestsFromTestCase(TestCatalog))
    suite.addTest(loader.loadTestsFromTestCase(TestBottler))
    suite.addTest(loader.loadTestsFromTestCase(TestBarrels))

    # Run the combined test suite
    runner = unittest.TextTestRunner()
    runner.run(suite)
