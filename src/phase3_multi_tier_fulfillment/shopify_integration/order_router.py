import shopify
import json
from typing import Dict
from config import PrintStrategy

class ShopifyOrderRouter:
    def __init__(self):
        self.setup_shopify_session()
    
    def setup_shopify_session(self):
        """Initialize Shopify API session"""
        shopify.ShopifyResource.set_site(
            f"https://{PrintStrategy.SHOPIFY_API_KEY}:{PrintStrategy.SHOPIFY_ACCESS_TOKEN}@{PrintStrategy.SHOPIFY_STORE_URL}.myshopify.com/admin/api/2023-10"
        )
    
    def route_order(self, order_data: Dict) -> Dict:
        """Route Shopify order to appropriate fulfillment platform"""
        try:
            order_id = order_data['id']
            line_items = order_data['line_items']
            
            # Group line items by fulfillment platform
            platform_orders = {}
            
            for item in line_items:
                # Get product metafields to determine fulfillment platform
                product_id = item['product_id']
                variant_id = item['variant_id']
                
                fulfillment_info = self._get_fulfillment_info(product_id)
                platform = fulfillment_info['platform']
                
                if platform not in platform_orders:
                    platform_orders[platform] = {
                        'order_id': order_id,
                        'items': [],
                        'customer': order_data['customer'],
                        'shipping_address': order_data['shipping_address'],
                        'billing_address': order_data['billing_address']
                    }
                
                platform_orders[platform]['items'].append({
                    'product_id': fulfillment_info['platform_product_id'],
                    'variant_id': variant_id,
                    'quantity': item['quantity'],
                    'shopify_line_item_id': item['id'],
                    'sku': item['sku']
                })
            
            # Send orders to respective platforms
            fulfillment_results = {}
            
            for platform, order_info in platform_orders.items():
                if platform == 'creativehub':
                    result = self._fulfill_via_creativehub(order_info)
                elif platform == 'whitewall':
                    result = self._fulfill_via_whitewall(order_info)
                elif platform == 'printify':
                    result = self._fulfill_via_printify(order_info)
                else:
                    result = {'success': False, 'error': f'Unknown platform: {platform}'}
                
                fulfillment_results[platform] = result
            
            return {
                'success': True,
                'order_id': order_id,
                'platform_orders': fulfillment_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'order_id': order_data.get('id')
            }
    
    def _get_fulfillment_info(self, product_id: int) -> Dict:
        """Get fulfillment platform info from product metafields"""
        product = shopify.Product.find(product_id)
        metafields = shopify.Metafield.find(owner_resource='product', owner_id=product_id)
        
        fulfillment_info = {
            'platform': 'unknown',
            'platform_product_id': None,
            'platform_data': {}
        }
        
        for metafield in metafields:
            if metafield.namespace == 'fulfillment':
                if metafield.key == 'platform':
                    fulfillment_info['platform'] = metafield.value
                elif metafield.key == 'platform_product_id':
                    fulfillment_info['platform_product_id'] = metafield.value
                elif metafield.key == 'platform_data':
                    fulfillment_info['platform_data'] = json.loads(metafield.value)
        
        return fulfillment_info
    
    def _fulfill_via_creativehub(self, order_info: Dict) -> Dict:
        """Send order to CreativeHub for fulfillment"""
        from ..creativehub_integration.order_handler import CreativeHubOrderHandler
        handler = CreativeHubOrderHandler()
        return handler.create_order(order_info)
    
    def _fulfill_via_whitewall(self, order_info: Dict) -> Dict:
        """Send order to WhiteWall for fulfillment"""
        from ..whitewall_integration.fulfillment_manager import WhiteWallFulfillmentManager
        manager = WhiteWallFulfillmentManager()
        return manager.create_order(order_info)
    
    def _fulfill_via_printify(self, order_info: Dict) -> Dict:
        """Send order to Printify for fulfillment"""
        from ..printify_integration.printify_client import PrintifyOrderManager
        manager = PrintifyOrderManager()
        return manager.create_order(order_info)1