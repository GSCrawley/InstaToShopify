#!/usr/bin/env python3
"""
Test script for the Instagram scraper component.
"""

import os
import sys
import argparse
import logging

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_scraper_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the scraper functionality
from src.phase1_acquisition.instagram_scraper import process_instagram_posts
from src import config

def parse_args():
    parser = argparse.ArgumentParser(description='Test Instagram Scraper')
    
    parser.add_argument('--profile', '-p', type=str,
                        help='Instagram profile URL to scrape (overrides .env)')
    
    parser.add_argument('--max-posts', '-m', type=int, default=10,
                        help='Maximum number of posts to scrape')
    
    parser.add_argument('--landscape-only', '-l', action='store_true', default=False,
                        help='Filter for landscape images only')
    
    parser.add_argument('--min-ratio', '-r', type=float, default=1.2,
                        help='Minimum width/height ratio for landscape filtering')
    
    parser.add_argument('--output-dir', '-o', type=str, default='data',
                        help='Directory to save downloaded images')
    
    parser.add_argument('--use-gcs', '-g', action='store_true', default=False,
                        help='Upload images to Google Cloud Storage')
                        
    parser.add_argument('--use-content-filter', '-cf', action='store_true', default=False,
                        help='Use Google Vision API for content filtering')
                        
    parser.add_argument('--content-terms', '-ct', type=str, default='',
                        help='Comma-separated list of content terms to filter by (e.g. "sunset,mountains,nature")')
    
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(args.output_dir, 'logs'), exist_ok=True)
    
    # Use profile from args or config
    profile_urls = None
    if args.profile:
        profile_urls = [args.profile]
        logger.info(f"Using profile URL from command line: {args.profile}")
    else:
        profile_urls = config.INSTAGRAM_TARGET_PROFILES
        logger.info(f"Using profile URLs from config: {profile_urls}")
    
    # Log configuration
    logger.info(f"Configuration:")
    logger.info(f"  Max posts: {args.max_posts}")
    logger.info(f"  Landscape only: {args.landscape_only}")
    logger.info(f"  Min landscape ratio: {args.min_ratio}")
    logger.info(f"  Output directory: {args.output_dir}")
    logger.info(f"  Use GCS: {args.use_gcs}")
    logger.info(f"  Use content filter: {args.use_content_filter}")
    if args.use_content_filter and args.content_terms:
        logger.info(f"  Content filter terms: {args.content_terms}")
    
    # Check if APIFY token is configured
    if not config.APIFY_API_TOKEN:
        logger.error("APIFY_API_TOKEN not set in environment. Please check your .env file.")
        return 1
    else:
        logger.info(f"Using Apify token: {config.APIFY_API_TOKEN[:5]}...")
    
    try:
        # Prepare content filter terms if provided
        content_filter_terms = None
        if args.content_terms:
            content_filter_terms = [term.strip() for term in args.content_terms.split(',') if term.strip()]
            
        # Process Instagram posts
        logger.info("Starting Instagram scraping process...")
        processed_posts = process_instagram_posts(
            profile_urls=profile_urls,
            max_posts=args.max_posts,
            landscape_only=args.landscape_only,
            min_landscape_ratio=args.min_ratio,
            base_dir=args.output_dir,
            use_gcs=args.use_gcs,
            content_filter_terms=content_filter_terms,
            use_content_filter=args.use_content_filter
        )
        
        # Log results
        if processed_posts:
            logger.info(f"Successfully processed {len(processed_posts)} posts.")
            for i, post in enumerate(processed_posts[:5]):  # Show details of first 5 posts
                logger.info(f"Post {i+1}:")
                logger.info(f"  Username: {post.get('owner_username')}")
                logger.info(f"  Shortcode: {post.get('shortcode')}")
                logger.info(f"  Local path: {post.get('local_path')}")
                logger.info(f"  Is landscape: {post.get('is_landscape')}")
                logger.info(f"  Hashtags: {post.get('hashtags')}")
                
                # Log content filter results if available
                if 'content_filter_results' in post:
                    filter_results = post['content_filter_results']
                    logger.info(f"  Content filter: {filter_results.get('meets_criteria', False)}")
                    logger.info(f"  Matched terms: {filter_results.get('matched_filters', [])}")
                
            if len(processed_posts) > 5:
                logger.info(f"... and {len(processed_posts) - 5} more posts")
        else:
            logger.warning("No posts were processed.")
            
        return 0
    
    except Exception as e:
        logger.error(f"Error processing Instagram posts: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
