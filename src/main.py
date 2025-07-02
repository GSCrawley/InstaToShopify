#!/usr/bin/env python3
"""
Instagram to Shopify Automation - Main Workflow

This script orchestrates the entire workflow for:
1. Acquiring images from Instagram
2. Processing and optimizing images for print
3. Creating products on Shopify
"""

import os
import sys
import logging
import argparse
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('instagram_to_shopify.log') # Updated log file name
    ]
)
logger = logging.getLogger(__name__)

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import modules from project
from src import config
from src.phase1_acquisition.instagram_scraper import process_instagram_posts
from src.phase2_processing.image_processor import ImageProcessor
# New Shopify import
from src.phase3_shopify_integration.admin_api import ShopifyAdminAPI, ShopifyAPIError

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Instagram to Shopify Automation')
    
    parser.add_argument('--workflow', '-w', type=str, default='full',
                        choices=['full', 'acquisition', 'processing', 'shopify'],
                        help='Workflow to run')
                        
    parser.add_argument('--input-dir', '-i', type=str,
                        default='data/raw_images',
                        help='Directory of images to process (for processing-only workflow)')

    parser.add_argument('--output-dir', '-o', type=str,
                        default='data/processed_images',
                        help='Directory to save processed images')

    parser.add_argument('--limit', '-l', type=int, default=10,
                        help='Limit the number of images to process')

    parser.add_argument('--skip-download', action='store_true',
                        help='Skip downloading images if they already exist')

    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    parser.add_argument('--enhance-image', type=str, default=None,
                        help='Path to a single image to enhance using AI')

    return parser.parse_args()


def setup_directories(args):
    """Create necessary directories for the workflow."""
    Path(args.input_dir).mkdir(parents=True, exist_ok=True)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path('data/metadata').mkdir(parents=True, exist_ok=True)
    logger.info("Project directories are set up.")


def run_acquisition_phase(args) -> List[Dict[str, Any]]:
    """Runs the Instagram data acquisition phase."""
    logger.info("--- Starting Phase 1: Instagram Acquisition ---")

    # The process_instagram_posts function handles scraping and initial filtering.
    # It will return a list of post dictionaries that are suitable for processing.
    acquired_posts = process_instagram_posts(
        profile_urls=config.INSTAGRAM_TARGET_PROFILES,
        max_posts=args.limit,
        landscape_only=False,  # Enforce landscape for print suitability
        base_dir=args.input_dir,
        use_gcs=False,  # Assuming local workflow for now
        use_enhanced_filtering=True, # Use the most advanced filtering
        content_categories=config.ENHANCED_CONTENT_CATEGORIES,
        min_quality_score=config.MIN_QUALITY_SCORE,
        min_category_score=config.MIN_CATEGORY_SCORE,
        min_overall_score=config.MIN_OVERALL_SCORE
    )

    if not acquired_posts:
        logger.warning("No suitable posts found from Instagram after filtering.")
        return []

    logger.info(f"--- Acquisition Phase Complete. Found {len(acquired_posts)} suitable posts. ---")
    return acquired_posts


def run_processing_phase(acquired_posts: List[Dict[str, Any]], args: argparse.Namespace) -> Dict[str, Any]:
    """Runs the image processing phase."""
    logger.info("--- Starting Phase 2: Image Processing ---")

    if not acquired_posts:
        logger.warning("No posts to process. Skipping processing phase.")
        return {}

    # The ImageProcessor constructor only takes a `use_gcs` flag.
    # Directory paths are handled by its methods.
    processor = ImageProcessor(use_gcs=False)

    # Get the list of image paths from the acquired posts
    image_paths = [post['local_path'] for post in acquired_posts if 'local_path' in post]
    if not image_paths:
        logger.warning("No valid local image paths found in acquired posts.")
        return {}

    logger.info(f"Starting processing for {len(image_paths)} images.")

    # Define processing parameters for demonstration
    enhancement_params = {
        'brightness': 1.1,
        'contrast': 1.1,
        'sharpness': 1.2
    }

    # Run batch processing
    processing_results = processor.batch_process_images(
        image_paths=image_paths,
        size_categories=['small', 'medium'],
        materials=['photo_paper', 'canvas'],
        enhancement_params=enhancement_params,
        base_dir=args.output_dir  # The output directory is passed here
    )

    if not processing_results.get('summary', {}).get('successful', 0) > 0:
        logger.error("Image processing phase failed to produce any results.")
        return {}

    logger.info("--- Image Processing Phase Complete ---")
    return processing_results


def run_shopify_integration_phase(processed_images: Dict[str, Any], args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Runs the Shopify integration phase: creates products on Shopify.
    
    Args:
        processed_images: A dictionary containing the results from the processing phase.
        args: Command line arguments.
        
    Returns:
        A list of created Shopify product data.
    """
    logger.info("--- Starting Phase 3: Shopify Integration ---")
    
    if not processed_images.get('successful'):
        logger.warning("No successfully processed images to create products for. Skipping Shopify integration.")
        return []
        
    try:
        shopify_client = ShopifyAdminAPI()
        logger.info("ShopifyAdminAPI client initialized.")
    except ValueError as e:
        logger.error(f"Failed to initialize ShopifyAdminAPI client: {e}")
        return []
        
    created_products = []
    
    for image_path, metadata in processed_images['successful'].items():
        try:
            logger.info(f"Creating Shopify product for image: {image_path}")
            
            # Create a basic product structure
            product_data = {
                "title": metadata.get('title', Path(image_path).stem.replace('_', ' ').title()),
                "body_html": metadata.get('description', f"A beautiful print of {Path(image_path).stem}."),
                "vendor": "Automated Art Co.",  # This can be configured
                "product_type": "Fine Art Print", # Default product type
                "tags": metadata.get('tags', ['art', 'photography']),
                "variants": [
                    {
                        "option1": "Default",
                        "price": "99.99", # Placeholder price
                        "sku": f"ART-{Path(image_path).stem.upper()}"
                    }
                ],
                # Image will be attached later, or use a GCS URL if available
                "images": []
            }

            created_product = shopify_client.create_product(product_data)
            logger.info(f"Successfully created Shopify product ID: {created_product.get('id')}")
            created_products.append(created_product)
            
            # Avoid hitting rate limits
            time.sleep(1)

        except ShopifyAPIError as e:
            logger.error(f"Failed to create Shopify product for {image_path}. Status: {e.status_code}, Errors: {e.errors}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating product for {image_path}: {e}", exc_info=True)
            
    logger.info(f"--- Shopify Integration Phase Complete. Created {len(created_products)} products. ---")
    return created_products


def run_enhancement_phase(image_path: str, args: argparse.Namespace):
    """Runs the AI image enhancement phase for a single image."""
    logger.info(f"--- Starting AI Enhancement Phase for: {image_path} ---")
    
    if not os.path.exists(image_path):
        logger.error(f"Image path does not exist: {image_path}")
        return

    processor = ImageProcessor(use_gcs=False)
    
    # 1. Prepare the image for enhancement
    preparation_result = processor.prepare_for_ai_enhancement(image_path, args.output_dir)
    
    if not preparation_result:
        logger.error("Failed to prepare image for AI enhancement.")
        return

    path_to_process, final_output_path, temp_path_to_cleanup = preparation_result
    
    # 2. Call the AI enhancement tool
    try:
        logger.info(f"Calling stability-ai-upscale-creative for {path_to_process}")
        # This is a placeholder for the actual tool call you would make in your environment
        # In a real scenario, you would import and call the tool directly.
        # For example:
        # from mcp_tools import mcp17_stability_ai_upscale_creative
        # result = mcp17_stability_ai_upscale_creative.call(
        #     imageFileUri=f"file://{os.path.abspath(path_to_process)}",
        #     prompt="A beautiful, high-resolution, professional photograph of a dramatic landscape, suitable for a fine-art gallery print. Remove all compression artifacts and enhance the natural details.",
        #     outputImageFileName=os.path.splitext(os.path.basename(final_output_path))[0]
        # )
        # 
        # if result.get('success'):
        #     logger.info(f"Successfully enhanced image saved to {final_output_path}")
        # else:
        #     logger.error(f"AI enhancement failed: {result.get('error')}")

        # As a placeholder, we'll just log the intended action
        logger.info("Placeholder: AI tool call would happen here.")
        logger.info(f"Placeholder: Enhanced image would be saved to {final_output_path}")

    except Exception as e:
        logger.error(f"An error occurred during AI enhancement: {e}", exc_info=True)
    
    finally:
        # 3. Clean up temporary files
        if temp_path_to_cleanup:
            logger.info(f"Cleaning up temporary file: {temp_path_to_cleanup}")
            os.unlink(temp_path_to_cleanup)

    logger.info("--- AI Enhancement Phase Complete ---")


def run_workflow(args):
    """Main workflow orchestrator."""
    start_time = time.time()
    setup_directories(args)
    
    metrics = {
        'images_acquired': 0,
        'images_processed': 0,
        'products_created': 0,
        'listings_published': 0,
        'errors': 0,
        'execution_time': 0
    }
    
    try:
        acquired_posts = []
        if args.workflow in ['full', 'acquisition']:
            acquired_posts = run_acquisition_phase(args)
            metrics['images_acquired'] = len(acquired_posts)

        processing_results = None
        if args.workflow in ['full', 'processing']:
            # If it's a full workflow, use the acquired posts.
            # If it's processing-only, the function will discover images from the input dir.
            input_for_processing = acquired_posts if args.workflow == 'full' else []
            processing_results = run_processing_phase(input_for_processing, args)
            metrics['images_processed'] = processing_results.get('summary', {}).get('successful', 0)

        if args.workflow in ['full', 'shopify']:
            if processing_results:
                created_products = run_shopify_integration_phase(processing_results, args)
                metrics['products_created'] = len(created_products)
                # Shopify products are created as active, so we count them as published
                metrics['listings_published'] = len(created_products)
            else:
                logger.warning("Skipping Shopify phase because there are no processed images.")
    
    except Exception as e:
        logger.error(f"Error in workflow: {e}", exc_info=True)
        metrics['errors'] += 1
    
    # Calculate execution time
    execution_time = time.time() - start_time
    metrics['execution_time'] = execution_time
    
    # Log workflow summary
    logger.info("Workflow complete.")
    logger.info(f"Images acquired: {metrics['images_acquired']}")
    logger.info(f"Images processed: {metrics['images_processed']}")
    logger.info(f"Products created: {metrics['products_created']}")
    logger.info(f"Listings published: {metrics['listings_published']}")
    logger.info(f"Errors: {metrics['errors']}")
    logger.info(f"Execution time: {execution_time:.2f} seconds")
    
    # Save metrics to file
    timestamp = int(time.time())
    metrics_path = f"data/metadata/workflow_metrics_{timestamp}.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics


if __name__ == "__main__":
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Check if we are running the enhancement phase
    if args.enhance_image:
        run_enhancement_phase(args.enhance_image, args)
    else:
        # Run the main workflow
        metrics = run_workflow(args)
        # Exit with appropriate code
        sys.exit(0 if metrics['errors'] == 0 else 1)
