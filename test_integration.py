#!/usr/bin/env python3
"""
Integration test for the Instagram to Etsy automation workflow.
This script tests the end-to-end flow including:
1. Image acquisition from Instagram with content filtering
2. Image processing for different print formats
3. Optional: Printify integration (dry run mode)
"""

import os
import sys
import logging
import argparse
import json
import time
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import project modules
from src.phase1_acquisition.instagram_scraper import process_instagram_posts
from src.phase1_acquisition.image_filter import ImageContentFilter
from src.phase2_processing.image_processor import ImageProcessor
from src.phase3_pod_integration.printify_api import PrintifyAPI
from src import config

def parse_args():
    """Parse command line arguments for the integration test."""
    parser = argparse.ArgumentParser(description='Instagram to Etsy Integration Test')
    
    parser.add_argument('--instagram-profile', '-p', type=str,
                        help='Instagram profile URL to test (overrides .env)')
    
    parser.add_argument('--max-posts', '-m', type=int, default=5,
                        help='Maximum number of posts to process')
    
    parser.add_argument('--landscape-only', '-l', action='store_true', default=True,
                        help='Filter for landscape images only')
    
    parser.add_argument('--content-filter', '-cf', action='store_true', default=False,
                        help='Enable content filtering with Google Vision API')
    
    parser.add_argument('--filter-terms', '-ft', type=str,
                        help='Comma-separated content terms (e.g., "sunset,mountains")')
    
    parser.add_argument('--printify-dryrun', '-pd', action='store_true', default=True,
                        help='Run Printify in dry-run mode (no actual product creation)')
    
    parser.add_argument('--skip-processing', '-sp', action='store_true', default=False,
                        help='Skip image processing phase')
    
    parser.add_argument('--base-dir', '-b', type=str, default='test_data',
                        help='Base directory for test data')
    
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    
    return parser.parse_args()

def test_instagram_acquisition(args) -> List[Dict[str, Any]]:
    """
    Test the Instagram acquisition phase with content filtering.
    
    Args:
        args: Command line arguments
        
    Returns:
        List of processed posts
    """
    logger.info("Testing Instagram acquisition phase")
    
    # Determine profile URLs
    profile_urls = None
    if args.instagram_profile:
        profile_urls = [args.instagram_profile]
        logger.info(f"Using profile URL from command line: {args.instagram_profile}")
    else:
        profile_urls = config.INSTAGRAM_TARGET_PROFILES
        if isinstance(profile_urls, str):
            profile_urls = profile_urls.split(',')
        logger.info(f"Using profile URLs from config: {profile_urls}")
    
    if not profile_urls:
        logger.error("No Instagram profile URLs specified")
        return []
    
    # Parse content filter terms if provided
    content_filter_terms = None
    if args.filter_terms:
        content_filter_terms = [term.strip() for term in args.filter_terms.split(',')]
        logger.info(f"Using content filter terms: {content_filter_terms}")
    elif hasattr(config, 'CV_CONTENT_DESCRIPTIONS_FILTER') and config.CV_CONTENT_DESCRIPTIONS_FILTER:
        content_filter_terms = [term.strip() for term in config.CV_CONTENT_DESCRIPTIONS_FILTER.split(',')]
        logger.info(f"Using content filter terms from config: {content_filter_terms}")
    
    # Create base directory for test data
    input_dir = os.path.join(args.base_dir, 'raw')
    os.makedirs(input_dir, exist_ok=True)
    
    # Process Instagram posts
    start_time = time.time()
    logger.info(f"Starting Instagram post processing with limit: {args.max_posts}")
    
    try:
        processed_posts = process_instagram_posts(
            profile_urls=profile_urls,
            max_posts=args.max_posts,
            landscape_only=args.landscape_only,
            min_landscape_ratio=1.2,  # Default landscape ratio
            base_dir=input_dir,
            use_gcs=False,  # Don't use GCS for testing
            content_filter_terms=content_filter_terms,
            use_content_filter=args.content_filter
        )
        
        execution_time = time.time() - start_time
        
        if processed_posts:
            logger.info(f"Successfully processed {len(processed_posts)} posts in {execution_time:.2f}s")
            
            # Log details of processed posts
            for i, post in enumerate(processed_posts, 1):
                logger.info(f"Post {i}:")
                logger.info(f"  Username: {post.get('owner_username')}")
                logger.info(f"  Post URL: https://www.instagram.com/p/{post.get('shortcode')}")
                logger.info(f"  Local path: {post.get('local_path')}")
                logger.info(f"  Is landscape: {post.get('is_landscape', False)}")
                
                # Log content filter results if available
                if 'content_filter_results' in post:
                    filter_results = post['content_filter_results']
                    meets_criteria = filter_results.get('meets_criteria', False)
                    matched_filters = filter_results.get('matched_filters', [])
                    
                    logger.info(f"  Meets content criteria: {meets_criteria}")
                    if matched_filters:
                        logger.info(f"  Matched filters: {matched_filters}")
            
            # Save results to file
            results_file = os.path.join(args.base_dir, 'acquisition_results.json')
            with open(results_file, 'w') as f:
                json.dump({
                    'posts_processed': len(processed_posts),
                    'execution_time': execution_time,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'config': {
                        'profile_urls': profile_urls,
                        'max_posts': args.max_posts,
                        'landscape_only': args.landscape_only,
                        'content_filter': args.content_filter,
                        'content_filter_terms': content_filter_terms
                    }
                }, f, indent=2)
                
            logger.info(f"Acquisition results saved to {results_file}")
            return processed_posts
        else:
            logger.warning("No posts were processed from Instagram")
            return []
            
    except Exception as e:
        logger.error(f"Error in Instagram acquisition phase: {e}", exc_info=True)
        return []

def test_printify_integration(processed_posts: List[Dict[str, Any]], processing_results: Dict[str, Any], args) -> Dict[str, Any]:
    """
    Test the Printify integration phase in dry-run mode.
    
    Args:
        processed_posts: List of processed posts from Instagram
        processing_results: Results from the image processing phase
        args: Command line arguments
        
    Returns:
        Dictionary with integration results
    """
    if not args.printify_dryrun:
        logger.info("Skipping Printify integration test (--printify-dryrun flag not set)")
        return {'skipped': True}
    
    logger.info("Testing Printify integration in dry-run mode")
    
    # Initialize Printify API client
    printify = PrintifyAPI()
    
    # Test connection to Printify
    try:
        logger.info("Testing connection to Printify API")
        shops = printify.get_shops()
        
        if not shops:
            logger.warning("No shops found in Printify account")
            return {'error': 'No shops found'}
            
        logger.info(f"Successfully connected to Printify. Found {len(shops)} shops.")
        
        # Get a test shop ID
        shop_id = shops[0]['id']
        logger.info(f"Using shop ID: {shop_id}")
        
        # Get print providers
        logger.info("Fetching print providers")
        blueprints = printify.find_wall_art_blueprints()
        
        if not blueprints:
            logger.warning("No wall art blueprints found")
            return {'error': 'No wall art blueprints found'}
            
        logger.info(f"Found {len(blueprints)} wall art blueprints")
        
        # Get the first blueprint for testing
        blueprint = blueprints[0]
        logger.info(f"Using blueprint: {blueprint['title']} (ID: {blueprint['id']})")
        
        # Get print providers for the blueprint
        print_providers = printify.get_print_providers(blueprint['id'])
        
        if not print_providers:
            logger.warning(f"No print providers found for blueprint {blueprint['id']}")
            return {'error': 'No print providers found'}
            
        logger.info(f"Found {len(print_providers)} print providers for blueprint {blueprint['id']}")
        
        # Prepare product data for a dry run test
        test_products = []
        
        # If we have processing results, use them
        if processing_results and 'results' in processing_results:
            results_dict = processing_results['results']
            logger.info(f"Preparing product data from {len(results_dict)} processed images")
            
            # Get up to 3 processed images for testing
            for i, (path, result) in enumerate(list(results_dict.items())[:3]):
                if not result.get('success', False):
                    continue
                    
                # Find a suitable variant
                variants = result.get('variants', {})
                variant_path = None
                
                # Try to find a medium size variant
                if 'medium' in variants and variants['medium']:
                    for size, materials in variants['medium'].items():
                        if 'fine_art_paper' in materials:
                            variant_path = materials['fine_art_paper'].get('local_path')
                            if variant_path:
                                break
                
                # If no medium variant, try any variant
                if not variant_path:
                    for size_cat, sizes in variants.items():
                        for size, materials in sizes.items():
                            for material, material_data in materials.items():
                                variant_path = material_data.get('local_path')
                                if variant_path:
                                    break
                            if variant_path:
                                break
                        if variant_path:
                            break
                
                if not variant_path or not os.path.exists(variant_path):
                    logger.warning(f"No suitable variant found for {path}")
                    continue
                
                # Extract metadata for title and description
                metadata = result.get('original_metadata', {})
                post_metadata = None
                
                # Find the original post metadata
                for post in processed_posts:
                    if post.get('local_path') == path:
                        post_metadata = post
                        break
                
                # Create test product data
                location = "Beautiful Location"
                if post_metadata and 'location' in post_metadata:
                    location = post_metadata['location']
                elif metadata and 'location' in metadata:
                    location = metadata['location']
                
                hashtags = []
                if post_metadata and 'hashtags' in post_metadata:
                    hashtags = post_metadata['hashtags']
                elif metadata and 'hashtags' in metadata:
                    hashtags = metadata['hashtags']
                
                # Create tags from hashtags
                tags = [tag.replace('#', '') for tag in hashtags[:13]]
                tags.extend(['wall art', 'landscape photography', 'fine art print', 'home decor'])
                tags = list(set(tags))[:13]  # Ensure uniqueness and limit
                
                test_product = {
                    'image_path': variant_path,
                    'title': f"Fine Art Print - {location} - Landscape Photography Wall Art",
                    'description': f"Beautiful landscape photography print of {location}. Perfect for home decor.",
                    'blueprint_id': blueprint['id'],
                    'print_provider_id': print_providers[0]['id'],
                    'tags': tags,
                    'dry_run': True  # Don't actually create the product
                }
                
                test_products.append(test_product)
                logger.info(f"Prepared test product {i+1}: {test_product['title']}")
        
        # If no test products from processing, create a dummy test
        if not test_products:
            logger.info("No processed images available. Creating dummy test product data.")
            test_products.append({
                'title': "Test Product - Landscape Photography",
                'description': "This is a test product for dry run mode.",
                'blueprint_id': blueprint['id'],
                'print_provider_id': print_providers[0]['id'],
                'tags': ['test', 'landscape', 'photography'],
                'dry_run': True
            })
        
        # Log test results
        results = {
            'success': True,
            'shops_found': len(shops),
            'blueprints_found': len(blueprints),
            'print_providers_found': len(print_providers),
            'test_products_prepared': len(test_products),
            'api_connection': 'successful',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save results to file
        results_file = os.path.join(args.base_dir, 'printify_test_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Printify test results saved to {results_file}")
        return results
        
    except Exception as e:
        logger.error(f"Error in Printify integration test: {e}", exc_info=True)
        return {'error': str(e)}

def test_image_processing(processed_posts: List[Dict[str, Any]], args) -> Dict[str, Any]:
    """
    Test the image processing phase.
    
    Args:
        processed_posts: List of processed posts from Instagram
        args: Command line arguments
        
    Returns:
        Dictionary with processing results
    """
    if args.skip_processing:
        logger.info("Skipping image processing phase (--skip-processing flag)")
        return {'skipped': True}
    
    logger.info("Testing image processing phase")
    
    # Extract image paths from processed posts
    image_paths = []
    for post in processed_posts:
        local_path = post.get('local_path')
        if local_path and os.path.exists(local_path):
            image_paths.append(local_path)
    
    if not image_paths:
        logger.warning("No valid image paths found for processing")
        return {'error': 'No valid images to process'}
    
    # Create output directory
    output_dir = os.path.join(args.base_dir, 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize image processor
    processor = ImageProcessor(use_gcs=False)  # Don't use GCS for testing
    
    # Process images
    start_time = time.time()
    logger.info(f"Processing {len(image_paths)} images")
    
    try:
        results = processor.batch_process_images(
            image_paths=image_paths,
            size_categories=['small', 'medium', 'large'],
            materials=['fine_art_paper', 'canvas', 'photo_paper'],
            fit_method='contain',
            base_dir=args.base_dir
        )
        
        execution_time = time.time() - start_time
        
        # Log processing results
        if results:
            summary = results.get('summary', {})
            logger.info(f"Processing complete in {execution_time:.2f}s")
            logger.info(f"  Successful: {summary.get('successful', 0)}")
            logger.info(f"  Failed: {summary.get('failed', 0)}")
            
            # Log details of first few processed images
            results_dict = results.get('results', {})
            for i, (path, result) in enumerate(list(results_dict.items())[:3]):
                logger.info(f"Image {i+1}: {os.path.basename(path)}")
                logger.info(f"  Success: {result.get('success', False)}")
                logger.info(f"  Variants: {len(result.get('variants', {}))}")
                
                # Log a few variant details
                variants = result.get('variants', {})
                for size, size_variants in list(variants.items())[:2]:
                    logger.info(f"  {size.capitalize()} variants:")
                    for dim, materials in list(size_variants.items())[:2]:
                        logger.info(f"    {dim}: {list(materials.keys())}")
            
            # Save results to file
            results_file = os.path.join(args.base_dir, 'processing_results.json')
            with open(results_file, 'w') as f:
                # Create a simplified version for JSON serialization
                serializable_results = {
                    'summary': summary,
                    'execution_time': execution_time,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'images_processed': len(results_dict),
                    'successful_images': summary.get('successful', 0),
                    'failed_images': summary.get('failed', 0)
                }
                json.dump(serializable_results, f, indent=2)
                
            logger.info(f"Processing results saved to {results_file}")
            return results
        else:
            logger.warning("No processing results returned")
            return {'error': 'No processing results'}
            
    except Exception as e:
        logger.error(f"Error in image processing phase: {e}", exc_info=True)
        return {'error': str(e)}

def main():
    """Run the integration test."""
    # Parse arguments
    args = parse_args()
    
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Create base directory
    os.makedirs(args.base_dir, exist_ok=True)
    
    # Record start time
    start_time = time.time()
    
    # Initialize test results
    test_results = {
        'acquisition': {'status': 'not_run'},
        'processing': {'status': 'not_run'},
        'printify': {'status': 'not_run'},
        'overall_status': 'failed',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Run Instagram acquisition test
        logger.info("Starting Instagram acquisition test")
        processed_posts = test_instagram_acquisition(args)
        
        if processed_posts:
            test_results['acquisition'] = {
                'status': 'success',
                'posts_processed': len(processed_posts)
            }
            logger.info(f"Acquisition test successful: {len(processed_posts)} posts processed")
        else:
            test_results['acquisition'] = {
                'status': 'failed',
                'posts_processed': 0
            }
            logger.warning("Acquisition test failed: No posts processed")
            
        # Run image processing test if we have posts
        if processed_posts:
            logger.info("Starting image processing test")
            processing_results = test_image_processing(processed_posts, args)
            
            if processing_results and 'error' not in processing_results:
                if processing_results.get('skipped', False):
                    test_results['processing'] = {
                        'status': 'skipped'
                    }
                    logger.info("Processing test skipped")
                else:
                    summary = processing_results.get('summary', {})
                    test_results['processing'] = {
                        'status': 'success',
                        'images_processed': summary.get('successful', 0),
                        'images_failed': summary.get('failed', 0)
                    }
                    logger.info(f"Processing test successful: {summary.get('successful', 0)} images processed")
            else:
                test_results['processing'] = {
                    'status': 'failed',
                    'error': processing_results.get('error', 'Unknown error')
                }
                logger.warning(f"Processing test failed: {processing_results.get('error', 'Unknown error')}")
                
            # Run Printify integration test if enabled
            if args.printify_dryrun:
                logger.info("Starting Printify integration test")
                printify_results = test_printify_integration(processed_posts, processing_results, args)
                
                if printify_results and 'error' not in printify_results:
                    if printify_results.get('skipped', False):
                        test_results['printify'] = {
                            'status': 'skipped'
                        }
                        logger.info("Printify test skipped")
                    else:
                        test_results['printify'] = {
                            'status': 'success',
                            'shops_found': printify_results.get('shops_found', 0),
                            'test_products_prepared': printify_results.get('test_products_prepared', 0)
                        }
                        logger.info(f"Printify test successful: {printify_results.get('test_products_prepared', 0)} test products prepared")
                else:
                    test_results['printify'] = {
                        'status': 'failed',
                        'error': printify_results.get('error', 'Unknown error')
                    }
                    logger.warning(f"Printify test failed: {printify_results.get('error', 'Unknown error')}")
        
        # Determine overall status
        if (test_results['acquisition']['status'] == 'success' and
            (test_results['processing']['status'] in ['success', 'skipped']) and
            (test_results['printify']['status'] in ['success', 'skipped'])):
            test_results['overall_status'] = 'success'
            logger.info("Integration test completed successfully")
        else:
            test_results['overall_status'] = 'failed'
            logger.warning("Integration test failed")
            
    except Exception as e:
        logger.error(f"Error during integration test: {e}", exc_info=True)
        test_results['error'] = str(e)
        
    # Calculate execution time
    execution_time = time.time() - start_time
    test_results['execution_time'] = execution_time
    
    # Save test results
    results_file = os.path.join(args.base_dir, 'integration_test_results.json')
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
        
    logger.info(f"Integration test completed in {execution_time:.2f}s")
    logger.info(f"Test results saved to {results_file}")
    
    # Return exit code based on test results
    return 0 if test_results['overall_status'] == 'success' else 1

if __name__ == "__main__":
    sys.exit(main())
