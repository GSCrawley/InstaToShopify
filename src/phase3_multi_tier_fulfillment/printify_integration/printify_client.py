# src/phase3_multi_tier_fulfillment/printify_integration/printify_client.py
import requests
from typing import Dict, List
from config import PrintStrategy

class PrintifyManager:
    def __init__(self):
        self.api_key = PrintStrategy.PRINTIFY_API_KEY
        self.store_id = PrintStrategy.PRINTIFY_STORE_ID
        self.base_url = "https://api.printify.com/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_canvas_product(self, image_data: Dict) -> Dict:
        """Create canvas print product on Printify"""
        try:
            # Upload image to Printify
            image_upload = self._upload_image(image_data['processed_path'])
            if not image_upload.get('success'):
                raise Exception("Image upload failed")
            
            image_id = image_upload['id']
            
            # Create product with canvas options
            product_data = self._build_canvas_product_data(image_data, image_id)
            
            response = requests.post(
                f'{self.base_url}/shops/{self.store_id}/products.json',
                headers=self.headers,
                json=product_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'platform': 'printify',
                    'product_id': result['id'],
                    'shopify_product_id': None,  # Will be set after Shopify sync
                    'variants': result['variants'],
                    'print_areas': result['print_areas']
                }
            else:
                raise Exception(f"Printify API error: {response.text}")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'printify'
            }
    
    def _upload_image(self, image_path: str) -> Dict:
        """Upload image to Printify"""
        with open(image_path, 'rb') as image_file:
            files = {'file': ('image.jpg', image_file, 'image/jpeg')}
            
            response = requests.post(
                f'{self.base_url}/uploads/images.json',
                headers={'Authorization': f'Bearer {self.api_key}'},
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                return {'success': True, 'id': result['id'], 'url': result['preview_url']}
            else:
                return {'success': False, 'error': response.text}
    
    def _build_canvas_product_data(self, image_data: Dict, image_id: str) -> Dict:
        """Build product data for canvas prints"""
        metadata = image_data.get('instagram_metadata', {})
        
        title = f"Canvas Print - {metadata.get('caption', 'Instagram Photography')[:50]}"
        description = f"""
High-quality canvas print perfect for home decoration. Printed on premium canvas 
material with fade-resistant inks.

- Premium canvas material
- Fade-resistant printing
- Multiple size options
- Ready to hang
- Perfect for home or office decor
        """.strip()
        
        return {
            "title": title,
            "description": description,
            "blueprint_id": 384,  # Canvas blueprint ID (verify this)
            "print_provider_id": 1,  # Default print provider
            "variants": [
                {
                    "id": 45740,  # 12x16 Canvas variant ID
                    "price": 2999,  # $29.99 in cents
                    "is_enabled": True
                },
                {
                    "id": 45741,  # 16x20 Canvas variant ID  
                    "price": 3999,  # $39.99 in cents
                    "is_enabled": True
                },
                {
                    "id": 45742,  # 20x24 Canvas variant ID
                    "price": 4999,  # $49.99 in cents
                    "is_enabled": True
                }
            ],
            "print_areas": [
                {
                    "variant_ids": [45740, 45741, 45742],
                    "placeholders": [
                        {
                            "position": "front",
                            "images": [
                                {
                                    "id": image_id,
                                    "x": 0.5,
                                    "y": 0.5,
                                    "scale": 1,
                                    "angle": 0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def sync_to_shopify(self, printify_product_id: str) -> Dict:
        """Sync Printify product to Shopify store"""
        response = requests.post(
            f'{self.base_url}/shops/{self.store_id}/products/{printify_product_id}/publishing_succeeded.json',
            headers=self.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'shopify_product_id': result.get('external_id'),
                'sync_status': 'completed'
            }
        else:
            return {
                'success': False,
                'error': f"Sync failed: {response.text}"
            }