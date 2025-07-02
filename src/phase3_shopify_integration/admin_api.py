# admin_api.py: Manages product creation, inventory, and other backend operations using the Shopify Admin API.

import requests
import json
import time
from typing import Dict, Any, List

from src import config

class ShopifyAPIError(Exception):
    """Custom exception for Shopify API errors."""
    def __init__(self, status_code: int, errors: Dict[str, Any]):
        self.status_code = status_code
        self.errors = errors
        message = f"Shopify API request failed with status {status_code}: {json.dumps(errors)}"
        super().__init__(message)

class ShopifyAdminAPI:
    """A client for interacting with the Shopify Admin API."""

    def __init__(self):
        """Initializes the Shopify Admin API client."""
        if not config.SHOPIFY_STORE_NAME or not config.SHOPIFY_ADMIN_API_TOKEN:
            raise ValueError("Shopify store name and admin API token must be set in config.")

        self.store_name = config.SHOPIFY_STORE_NAME
        self.api_token = config.SHOPIFY_ADMIN_API_TOKEN
        self.api_version = "2024-04"  # Use a recent, stable API version
        self.base_url = f"https://{self.store_name}.myshopify.com/admin/api/{self.api_version}"
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.api_token,
        }
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Makes a request to the Shopify API and handles responses."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                print(f"Rate limit hit. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                return self._request(method, endpoint, **kwargs)

            return response.json()
        except requests.exceptions.HTTPError as http_err:
            try:
                errors = http_err.response.json().get('errors', {})
            except json.JSONDecodeError:
                errors = {'error': http_err.response.text}
            raise ShopifyAPIError(status_code=http_err.response.status_code, errors=errors) from http_err
        except requests.exceptions.RequestException as req_err:
            raise ShopifyAPIError(status_code=500, errors={'error': str(req_err)}) from req_err

    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new product in Shopify.

        Args:
            product_data: A dictionary containing the product details.
                          Example:
                          {
                              "title": "Beautiful Landscape",
                              "body_html": "<strong>A stunning landscape photo.</strong>",
                              "vendor": "Your Brand Name",
                              "product_type": "Fine Art Print",
                              "tags": ["landscape", "nature", "art"],
                              "variants": [
                                  {
                                      "option1": "12x18",
                                      "price": "45.00",
                                      "sku": "ART-LS-1218"
                                  }
                              ],
                              "images": [
                                  {"src": "http://example.com/image.jpg"}
                              ]
                          }

        Returns:
            A dictionary representing the newly created product.
        """
        endpoint = "products.json"
        payload = {"product": product_data}
        response = self._request("POST", endpoint, json=payload)
        return response.get("product", {})

# Example usage for testing
if __name__ == '__main__':
    print("Testing ShopifyAdminAPI client...")
    try:
        client = ShopifyAdminAPI()
        print("Client initialized successfully.")

        # --- Test Product Creation ---
        test_product = {
            "title": "[Test] Sunset Over the Mountains",
            "body_html": "A beautiful test product created via the API.",
            "vendor": "Automated Art Co.",
            "product_type": "Test Print",
            "tags": ["test", "api", "example"],
            "variants": [
                {
                    "option1": "Small",
                    "price": "19.99",
                    "sku": "TEST-ART-SML-01"
                },
                {
                    "option1": "Large",
                    "price": "39.99",
                    "sku": "TEST-ART-LRG-01"
                }
            ],
            # In a real scenario, you would upload an image to Shopify first
            # or provide a publicly accessible URL.
        }

        print(f"\nAttempting to create a test product: {test_product['title']}")
        created_product = client.create_product(test_product)
        print("\n✅ Successfully created product:")
        print(json.dumps(created_product, indent=2))

        product_id = created_product.get('id')
        if product_id:
            print(f"\nProduct ID: {product_id}")
            print(f"View it here: https://{client.store_name}.myshopify.com/admin/products/{product_id}")

    except ValueError as ve:
        print(f"\n❌ Configuration Error: {ve}")
        print("Please ensure your .env file is correctly set up with Shopify credentials.")
    except ShopifyAPIError as e:
        print(f"\n❌ Shopify API Error (Status {e.status_code}):")
        print(json.dumps(e.errors, indent=2))
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")