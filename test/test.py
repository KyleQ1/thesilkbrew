import unittest
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class maintesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_api_key = os.getenv("API_KEY")
        assert cls.admin_api_key is not None, "API key must not be None"
        cls.base_url = "http://localhost:3000/"
        cls.header = {"access_token": cls.admin_api_key}

    def test_audit(self):
        response = requests.get('http://localhost:3000/inventory/audit', headers=self.header)
        
        self.assertEqual(response.status_code, 200)

    def test_capacity_plan(self):
        h = {'access_token': self.admin_api_key}
        response = requests.post('http://localhost:3000/inventory/plan', headers=self.header)
        self.assertEqual(response.status_code, 200)
    
    def test_deliver_capacity_plan(self):
        response = requests.post('http://localhost:3000/inventory/deliver/1', headers=self.header, json=
                                 {"potion_capacity": 0, "ml_capacity": 0})
        self.assertEqual(response.status_code, 200)
    
    def test_cart(self):
        response = requests.get('http://localhost:3000/cart', headers=self.header)
        self.assertEqual(response.status_code, 200)
    


if __name__ == '__main__':
    unittest.main()