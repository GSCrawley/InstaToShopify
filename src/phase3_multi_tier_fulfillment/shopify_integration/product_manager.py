import shopify 
from typing import Dict, List, Optional
from config import PrintStrategy

class ShopifyProductManager:
    def __init__(self):
        self.setup_shopify_session()
        
    def setup_shopify_session(self):
        """Initialize Shopify API session"""
        shopify.ShopifyResource.set_site(
            f"https://{PrintStrategy.SHOPIFY_API_KEY}:{PrintStrategy.SHOPIFY_ACCESS_TOKEN}@{PrintStrategy.SHOPIFY_STORE_URL}.myshopify.com/admin/api/2023-10"
        )
    
    def create_unified_product(self, image_data: Dict, fulfillment_platform: str, platform_product_data: Dict) -> Dict:
        """Create product in Shopify regardless of fulfillment partner"""
        try:
            metadata = self._generate_unified_metadata(image_data, fulfillment_platform, platform_product_data)
            
            # Create Shopify product
            product = shopify.Product()
            product.title = metadata['title']
            product.body_html = metadata['description']
            product.vendor = "Instagram Fine Art Photography"
            product.product_type = metadata['product_type']
            product.tags = metadata['tags']
            
            # Add variants based on fulfillment platform
            product.variants = self._create_variants(platform_product_data, fulfillment_platform)
            
            # Add images
            product.images = [shopify.Image({'src': image_data['processed_url']})]
            
            if product.save():
                # Add metafields for fulfillment routing
                self._add_fulfillment_metafields(product.id, fulfillment_platform, platform_product_data)
                
                return {
                    'success': True,
                    'shopify_product_id': product.id,
                    'platform': fulfillment_platform,
                    'platform_product_id': platform_product_data.get('product_id'),
                    'variants': [{'id': v.id, 'price': v.price, 'title': v.title} for v in product.variants]
                }
            else:
                raise Exception(f"Shopify product creation failed: {product.errors.full_messages()}")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': fulfillment_platform
            }
    
    def _generate_unified_metadata(self, image_data: Dict, fulfillment_platform: str, platform_data: Dict) -> Dict:
        """Generate unified metadata for Shopify regardless of platform"""
        instagram_data = image_data.get('instagram_metadata', {})
        cv_analysis = image_data.get('cv_analysis', {})
        quality_score = image_data.get('enhanced_score', 0)
        
        # Determine product tier and type
        if quality_score >= PrintStrategy.QUALITY_THRESHOLD_PREMIUM:
            product_type = "Fine Art Print"
            tier = "Premium"
        elif quality_score >= PrintStrategy.QUALITY_THRESHOLD_PROFESSIONAL:
            product_type = "Professional Print"
            tier = "Professional"
        else:
            product_type = "Canvas Print"
            tier = "Canvas"
        
        # Generate title and description
        location = self._extract_location(instagram_data.get('hashtags', []))
        title = f"{location} {product_type} - Instagram Photography"
        
        description = self._generate_tier_description(tier, fulfillment_platform, location)
        
        # Generate tags for organization and fulfillment routing
        tags = [
            f"tier:{tier.lower()}",
            PrintStrategy.FULFILLMENT_TAGS[fulfillment_platform],
            f"quality:{quality_score:.2f}",
            f"location:{location.lower()}",
            "instagram-photography",
            product_type.lower().replace(' ', '-')
        ]
        
        return {
            'title': title,
            'description': description,
            'product_type': product_type,
            'tags': ','.join(tags),
            'tier': tier,
            'location': location
        }
    
    def _create_variants(self, platform_data: Dict, fulfillment_platform: str) -> List:
        """Create Shopify variants based on platform capabilities"""
        variants = []
        
        if fulfillment_platform == 'creativehub':
            # Use CreativeHub print options
            print_options = platform_data.get('product_details', {}).get('PrintOptions', [])
            pricing = platform_data.get('pricing', {})
            
            for option in print_options:
                if option.get('IsAvailable') and option['Id'] in pricing:
                    price_info = pricing[option['Id']]
                    variant = shopify.Variant({
                        'title': price_info['size'],
                        'price': price_info['retail_price'],
                        'sku': f"CH-{platform_data.get('product_id')}-{option['Id']}",
                        'inventory_management': None,  # CreativeHub handles inventory
                        'requires_shipping': True
                    })
                    variants.append(variant)
        
        elif fulfillment_platform == 'whitewall':
            # WhiteWall premium options
            sizes = [
                {'title': '8x10 inch', 'price': 89.99, 'sku': f"WW-{platform_data.get('product_id')}-8x10"},
                {'title': '11x14 inch', 'price': 129.99, 'sku': f"WW-{platform_data.get('product_id')}-11x14"},
                {'title': '16x20 inch', 'price': 189.99, 'sku': f"WW-{platform_data.get('product_id')}-16x20"}
            ]
            
            for size in sizes:
                variant = shopify.Variant(size)
                variant.requires_shipping = True
                variants.append(variant)
        
        elif fulfillment_platform == 'printify':
            # Use Printify variants
            printify_variants = platform_data.get('variants', [])
            
            for pv in printify_variants:
                variant = shopify.Variant({
                    'title': f"Canvas {pv.get('title', 'Print')}",
                    'price': pv.get('price', 0) / 100,  # Printify prices are in cents
                    'sku': f"PF-{platform_data.get('product_id')}-{pv.get('id')}",
                    'inventory_management': None,  # Printify handles inventory
                    'requires_shipping': True
                })
                variants.append(variant)