# src/main_multi_tier.py
import logging
from typing import Dict, List
from datetime import datetime

# Import existing modules
from phase1_acquisition.enhanced_instagram_acquisition import enhanced_instagram_acquisition
from phase2_processing.batch_image_processing import batch_image_processing

# Import new multi-tier modules
from phase3_multi_tier_fulfillment.quality_router import QualityBasedRouter
from phase3_multi_tier_fulfillment.monitoring.health_checker import PlatformHealthMonitor
from phase3_multi_tier_fulfillment.monitoring.performance_tracker import PerformanceTracker

def main_multi_tier_workflow():
    """Enhanced workflow with multi-tier fulfillment strategy"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/multi_tier_workflow.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting multi-tier Instagram-to-print workflow")
    
    # Initialize components
    router = QualityBasedRouter()
    health_monitor = PlatformHealthMonitor()
    performance_tracker = PerformanceTracker()
    
    try:
        # Phase 1: Check platform health
        logger.info("Checking platform health...")
        health_check = health_monitor.check_all_platforms()
        logger.info(f"Overall health: {health_check['overall_health']}")
        
        for recommendation in health_check['routing_recommendations']:
            logger.info(f"Routing recommendation: {recommendation}")
        
        # Phase 2: Instagram acquisition (existing)
        logger.info("Starting Instagram image acquisition...")
        instagram_results = enhanced_instagram_acquisition()
        
        if not instagram_results.get('images'):
            logger.warning("No images acquired from Instagram")
            return
        
        logger.info(f"Acquired {len(instagram_results['images'])} images")
        
        # Phase 3: Image processing (existing + enhancements)
        logger.info("Processing images...")
        processed_images = batch_image_processing(instagram_results['images'])
        
        # Phase 4: Quality-based routing and unified product creation
        logger.info("Starting quality-based product creation...")
        
        creation_results = {
            'total_processed': 0,
            'successful_creations': 0,
            'failed_creations': 0,
            'platform_breakdown': {
                'creativehub': 0,
                'whitewall': 0,
                'printify': 0
            },
            'tier_breakdown': {
                'premium': 0,
                'professional': 0,
                'canvas': 0,
                'rejected': 0
            },
            'shopify_products': []
        }
        
        for image_data in processed_images:
            creation_results['total_processed'] += 1
            
            # Route image and create unified product (platform + Shopify)
            routing_result = router.route_and_create_product(image_data)
            
            if routing_result.get('success'):
                creation_results['successful_creations'] += 1
                platform = routing_result.get('primary_platform', 'unknown')
                creation_results['platform_breakdown'][platform] += 1
                
                # Track tier
                tier = routing_result.get('tier', 'unknown')
                creation_results['tier_breakdown'][tier] += 1
                
                # Store Shopify product info
                creation_results['shopify_products'].append({
                    'shopify_id': routing_result['shopify_product_id'],
                    'platform_id': routing_result['platform_product_id'],
                    'fulfillment_platform': routing_result['fulfillment_platform'],
                    'tier': tier,
                    'quality_score': routing_result['quality_score']
                })
                
                logger.info(
                    f"Created unified product: "
                    f"Shopify ID={routing_result['shopify_product_id']}, "
                    f"Platform={platform}, "
                    f"Tier={tier}, "
                    f"Quality={routing_result['quality_score']:.3f}"
                )
                
                # Track performance
                performance_tracker.record_success(platform, routing_result['quality_score'])
                
            else:
                creation_results['failed_creations'] += 1
                reason = routing_result.get('reason', 'unknown')
                
                if reason == 'quality_too_low':
                    creation_results['tier_breakdown']['rejected'] += 1
                
                logger.warning(
                    f"Failed to create unified product: {reason} "
                    f"(quality: {routing_result.get('quality_score', 'N/A')})"
                )
                
                # Track performance
                performance_tracker.record_failure(
                    routing_result.get('attempted_platforms', []),
                    reason
                )
        
        # Phase 5: Generate summary report
        logger.info("Workflow completed. Generating summary...")
        
        summary = {
            'workflow_start': datetime.now().isoformat(),
            'platform_health': health_check,
            'creation_results': creation_results,
            'performance_metrics': performance_tracker.get_summary(),
            'routing_stats': router.get_routing_stats()
        }
        
        # Log summary
        logger.info("=== WORKFLOW SUMMARY ===")
        logger.info(f"Total images processed: {creation_results['total_processed']}")
        logger.info(f"Successful creations: {creation_results['successful_creations']}")
        logger.info(f"Failed creations: {creation_results['failed_creations']}")
        logger.info(f"Success rate: {(creation_results['successful_creations'] / creation_results['total_processed'] * 100):.1f}%")
        
        logger.info("Platform breakdown:")
        for platform, count in creation_results['platform_breakdown'].items():
            logger.info(f"  {platform}: {count}")
        
        logger.info("Tier breakdown:")
        for tier, count in creation_results['tier_breakdown'].items():
            logger.info(f"  {tier}: {count}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Workflow failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main_multi_tier_workflow()