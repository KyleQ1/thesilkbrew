import unittest
import requests
from dotenv import load_dotenv
import os

load_dotenv()
        
class TestBarrels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}
    
    def test_purchasing(self):
        barrels = [
            {"sku": "MINI_RED_BARREL", "ml_per_barrel": 500, "potion_type": [1, 0, 0, 0],  
             "price": 100, "quantity": 10}, 
             {"sku": "MINI_GREEN_BARREL", "ml_per_barrel": 500, "potion_type": [0, 1, 0, 0],
              "price": 100, "quantity": 10},
            {"sku": "MINI_RED_BARREL", "ml_per_barrel": 500, "potion_type": [0, 0, 1, 0],
              "price": 100, "quantity": 10},
            {"sku": "MINI_DARK_BARREL", "ml_per_barrel": 500, "potion_type": [0, 0, 0, 1],
              "price": 500, "quantity": 10}]
        response = requests.post('http://localhost:3000/barrels/plan', json=barrels, headers=self.header)
        self.assertEqual(response.status_code, 200)

        purchased_barrels = response.json()
        adjusted_barrels = []
        for purchased_barrel in purchased_barrels:
            for barrel in barrels:
                if barrel['sku'] == purchased_barrel['sku']:
                    # Modify the quantity to the purchased quantity for delivery
                    barrel['quantity'] = purchased_barrel['quantity']
                    adjusted_barrels.append(barrel)
    
        response2 = requests.post('http://localhost:3000/barrels/deliver/1', json=adjusted_barrels, 
                                  headers=self.header)
        self.assertEqual(response2.status_code, 200)

class TestBottler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}
    
    def test_bottling(self):
        response = requests.post('http://localhost:3000/bottler/plan', headers=self.header)
        self.assertEqual(response.status_code, 200)
        response2 = requests.post('http://localhost:3000/bottler/deliver/1', json=response.json(), 
                                  headers=self.header)
        self.assertEqual(response2.status_code, 200)

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
    # Combine these two tests
    def test_plan(self):
        response1 = requests.post('http://localhost:3000/inventory/plan', headers=self.header)
        self.assertEqual(response1.status_code, 200) 
        response2 = requests.post('http://localhost:3000/inventory/deliver/1', headers=self.header, json=
                                 response1.json())
        self.assertEqual(response2.status_code, 200)
        

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

    @unittest.skip
    def test_visits(self):
        response = requests.get('http://localhost:3000/carts/visits/1', headers=self.header, 
                                json=[{"customer_name": "John Doe", "character_class": "Warrior", "level": 1}])
        self.assertEqual(response.status_code, 200)

    def test_cart_process(self):
        catalog = requests.get('http://localhost:3000/catalog')
        self.assertEqual(catalog.status_code, 200)
        cat = catalog.json()[0]
        response = requests.post('http://localhost:3000/carts/', headers=self.header, 
                                 json={"customer_name": "John Doe", "character_class": "Warrior", "level": 1})
        self.assertEqual(response.status_code, 200)
        id = response.json()["cart_id"]
        response = requests.post(f"http://localhost:3000/carts/{id}/items/{cat['sku']}", headers=self.header, 
                                 json={"quantity": max(1, cat["quantity"]-1)})
        self.assertEqual(response.status_code, 200)
        response = requests.post(f'http://localhost:3000/carts/{id}/checkout', headers=self.header,
                                 json={"payment": "gold"})
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    #suite.addTest(loader.loadTestsFromTestCase(TestBarrels))
    #suite.addTest(loader.loadTestsFromTestCase(TestBottler))
    #suite.addTest(loader.loadTestsFromTestCase(TestCatalog))
    suite.addTest(loader.loadTestsFromTestCase(TestInventory))
    #suite.addTest(loader.loadTestsFromTestCase(TestCarts))

    # Run the combined test suite
    runner = unittest.TextTestRunner()
    runner.failfast = True
    runner.run(suite)
