import requests
import json
from typing import Dict, List, Optional
from config import PrintStrategy

class CreativeHubClient:
    def __init__(self, use_sandbox: bool = False):
        self.api_key = PrintStrategy.CREATIVEHUB_SANDBOX_KEY if use_sandbox else PrintStrategy.CREATIVEHUB_API_KEY
        self.base_url = PrintStrategy.CREATIVEHUB_SANDBOX_URL if use_sandbox else PrintStrategy.CREATIVEHUB_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def upload_image(self, image_path: str, metadata: Dict) -> Dict:
        """Upload image file to CreativeHub"""
        files = {'file': open(image_path, 'rb')}
        upload_headers = {'Authorization': f'Bearer {self.api_key}'}
        
        response = requests.post(
            f'{self.base_url}/api/v1/products',
            files=files,
            headers=upload_headers,
            data={
                'DisplayName': metadata.get('title'),
                'Description': metadata.get('description'),
                'ArtistName': metadata.get('artist_name', 'Instagram Photography'),
                'Paper': 'Hahnemühle Photo Rag',
                'PrintType': 'Giclée'
            }
        )
        return response.json()
    
    def get_product(self, product_id: int) -> Dict:
        """Retrieve product details"""
        response = requests.get(
            f'{self.base_url}/api/v1/products/{product_id}',
            headers=self.headers
        )
        return response.json()
    
    def query_products(self, page: int = 1, page_size: int = 10) -> Dict:
        """Query all products"""
        payload = {
            "Page": page - 1,  # CreativeHub uses 0-based indexing
            "PageSize": page_size
        }
        response = requests.post(
            f'{self.base_url}/api/v1/products/query',
            headers=self.headers,
            json=payload
        )
        return response.json()
    
    def create_embryonic_order(self, order_data: Dict) -> Dict:
        """Create an embryonic order to get delivery options"""
        response = requests.post(
            f'{self.base_url}/api/v1/orders/embryonic',
            headers=self.headers,
            json=order_data
        )
        return response.json()
    
    def confirm_order(self, order_confirmation: Dict) -> Dict:
        """Confirm an order for processing"""
        response = requests.post(
            f'{self.base_url}/api/v1/orders/confirmed',
            headers=self.headers,
            json=order_confirmation
        )
        return response.json()
    
    def get_order(self, order_id: int) -> Dict:
        """Get order details"""
        response = requests.get(
            f'{self.base_url}/api/v1/orders/{order_id}',
            headers=self.headers
        )
        return response.json()
    
    def query_orders(self, page: int = 1, page_size: int = 10) -> Dict:
        """Query all orders"""
        payload = {
            "Page": page - 1,
            "PageSize": page_size
        }
        response = requests.post(
            f'{self.base_url}/api/v1/orders/query',
            headers=self.headers,
            json=payload
        )
        return response.json()