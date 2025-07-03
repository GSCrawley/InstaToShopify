# Routes images based on quality scores

from typing import Dict, List, Optional
from config import PrintStrategy
from .shopify_integration.product_manager import ShopifyProductManager
import logging

class QualityBasedRouter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.shopify_manager = ShopifyProductManager()
        
    def route_and_create_product(self, image_data: Dict) -> Dict:
        """Route image to appropriate platform and create unified Shopify product"""
        quality_score = image_data.get('enhanced_score', 0)
        
        # Determine tier and platform priority based on quality score
        if quality_score >= PrintStrategy.QUALITY_THRESHOLD_PREMIUM:
            tier = 'premium'
            platforms = ['creativehub', 'whitewall']
        elif quality_score >= PrintStrategy.QUALITY_THRESHOLD_PROFESSIONAL:
            tier = 'professional'
            platforms = ['whitewall', 'creativehub']
        elif quality_score >= PrintStrategy.QUALITY_THRESHOLD_CANVAS:
            tier = 'canvas'
            platforms = ['printify', 'whitewall']
        else:
            # Below minimum threshold, skip
            return {
                'success': False,
                'reason': 'quality_too_low',
                'quality_score': quality_score,
                'minimum_required': PrintStrategy.QUALITY_THRESHOLD_CANVAS
            }
        
        # Attempt product creation on each platform in priority order
        for platform in platforms:
            try:
                # Step 1: Create product on fulfillment platform
                platform_result = self._create_on_platform(platform, image_data, tier)
                
                if platform_result.get('success'):
                    # Step 2: Create unified product in Shopify
                    shopify_result = self.shopify_manager.create_unified_product(
                        image_data, 
                        platform, 
                        platform_result
                    )
                    
                    if shopify_result.get('success'):
                        self.logger.info(
                            f"Successfully created {tier} product: "
                            f"Platform={platform}, "
                            f"Quality={quality_score:.3f}, "
                            f"Shopify ID={shopify_result['shopify_product_id']}, "
                            f"Platform ID={platform_result.get('product_id')}"
                        )
                        
                        return {
                            'success': True,
                            'tier': tier,
                            'primary_platform': platform,
                            'quality_score': quality_score,
                            'shopify_product_id': shopify_result['shopify_product_id'],
                            'platform_product_id': platform_result.get('product_id'),
                            'fulfillment_platform': platform,
                            'variants': shopify_result.get('variants', [])
                        }
                    else:
                        self.logger.error(
                            f"Platform creation succeeded but Shopify creation failed: "
                            f"{shopify_result.get('error')}"
                        )
                        # Could implement cleanup of platform product here
                        continue
                else:
                    self.logger.warning(
                        f"Failed to create on {platform}: {platform_result.get('error')}"
                    )
            except Exception as e:
                self.logger.error(f"Error with {platform}: {str(e)}")
                continue
        
        # All platforms failed
        return {
            'success': False,
            'reason': 'all_platforms_failed',
            'quality_score': quality_score,
            'tier': tier,
            'attempted_platforms': platforms
        }
    
    def _create_on_platform(self, platform: str, image_data: Dict, tier: str) -> Dict:
        """Create product on specified fulfillment platform (not Shopify)"""
        if platform == 'creativehub':
            from .creativehub_integration.product_creator import CreativeHubProductCreator
            creator = CreativeHubProductCreator()
            return creator.create_premium_product(image_data)
            
        elif platform == 'whitewall':
            from .whitewall_integration.fulfillment_manager import WhiteWallProductCreator
            creator = WhiteWallProductCreator()
            return creator.create_professional_product(image_data, tier)
            
        elif platform == 'printify':
            from .printify_integration.printify_client import PrintifyManager
            manager = PrintifyManager()
            return manager.create_canvas_product(image_data)
            
        else:
            raise ValueError(f"Unknown platform: {platform}")
    
    def get_routing_stats(self) -> Dict:
        """Get statistics about routing decisions"""
        # This would track routing decisions over time
        return {
            'total_processed': 0,
            'premium_count': 0,
            'professional_count': 0,
            'canvas_count': 0,
            'rejected_count': 0,
            'platform_success_rates': {
                'creativehub': 0.0,
                'whitewall': 0.0,
                'printify': 0.0
            },
            'shopify_integration_success_rate': 0.0
        }