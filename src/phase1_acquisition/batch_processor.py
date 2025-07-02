#!/usr/bin/env python3
"""
Batch Processing System for Instagram to Etsy Workflow

Handles iterative scraping and processing until target number of accepted images is reached.
Integrates with image tracking to avoid duplicates and supports GCS for large batches.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import time

from .. import config
from ..utils.image_tracker import ImageTracker
from ..utils.gcs_storage import GCSStorage
from .instagram_scraper import (
    initialize_apify_client, 
    run_instagram_scraper_for_profiles, 
    get_scraped_data,
    download_images_from_posts,
    extract_post_metadata
)
from .enhanced_content_filter import EnhancedContentFilter

logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Handles batch processing of Instagram images with iterative scraping
    until target number of accepted images is reached.
    """
    
    def __init__(self, base_dir: str = 'data', use_gcs: bool = True):
        """
        Initialize the batch processor.
        
        Args:
            base_dir: Base directory for local storage
            use_gcs: Whether to use Google Cloud Storage
        """
        self.base_dir = base_dir
        self.use_gcs = use_gcs
        
        # Initialize components
        self.tracker = ImageTracker(base_dir)
        self.gcs = GCSStorage() if use_gcs else None
        self.enhanced_filter = EnhancedContentFilter(use_google_vision=True)
        
        # Initialize Apify client
        try:
            self.apify_client = initialize_apify_client()
            logger.info("Batch processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Apify client: {e}")
            self.apify_client = None
        
        # Check GCS availability
        if self.use_gcs and self.gcs and not self.gcs.is_available():
            logger.warning("GCS not available, falling back to local storage only")
            self.use_gcs = False
    
    def process_batch(self, 
                     target_count: int = 10,
                     profile_urls: List[str] = None,
                     content_categories: List[str] = None,
                     min_quality_score: float = None,
                     min_category_score: float = None,
                     min_overall_score: float = None,
                     max_iterations: int = 10,
                     posts_per_iteration: int = 50) -> Dict[str, Any]:
        """
        Process Instagram posts in batches until target number of accepted images is reached.
        
        Args:
            target_count: Target number of accepted images
            profile_urls: Instagram profile URLs to scrape
            content_categories: Content categories for filtering
            min_quality_score: Minimum quality score
            min_category_score: Minimum category score  
            min_overall_score: Minimum overall score
            max_iterations: Maximum number of scraping iterations
            posts_per_iteration: Number of posts to fetch per iteration
            
        Returns:
            Dictionary with batch processing results
        """
        if not self.apify_client:
            raise ValueError("Apify client not initialized")
        
        # Use config defaults if not provided
        if not profile_urls:
            profile_urls = config.INSTAGRAM_TARGET_PROFILES
        if not content_categories:
            content_categories = getattr(config, 'ENHANCED_CONTENT_CATEGORIES', ['landscape', 'sunset', 'water', 'nature', 'mountains'])
        if min_quality_score is None:
            min_quality_score = getattr(config, 'MIN_QUALITY_SCORE', 0.5)
        if min_category_score is None:
            min_category_score = getattr(config, 'MIN_CATEGORY_SCORE', 0.5)
        if min_overall_score is None:
            min_overall_score = getattr(config, 'MIN_OVERALL_SCORE', 0.6)
        
        logger.info(f"Starting batch processing: target={target_count}, max_iterations={max_iterations}")
        logger.info(f"Filtering criteria: quality≥{min_quality_score}, category≥{min_category_score}, overall≥{min_overall_score}")
        
        # Track processing metrics
        start_time = time.time()
        total_posts_scraped = 0
        total_posts_processed = 0
        accepted_images = []
        iteration_results = []
        
        # Check existing accepted images
        existing_accepted = self.tracker.get_accepted_images()
        logger.info(f"Found {len(existing_accepted)} previously accepted images")
        
        for iteration in range(max_iterations):
            logger.info(f"\n--- Iteration {iteration + 1}/{max_iterations} ---")
            
            # Check if we've reached our target
            current_accepted_count = len(accepted_images) + len(existing_accepted)
            if current_accepted_count >= target_count:
                logger.info(f"Target reached! Have {current_accepted_count} accepted images (target: {target_count})")
                break
            
            remaining_needed = target_count - current_accepted_count
            logger.info(f"Need {remaining_needed} more accepted images")
            
            # Scrape posts for this iteration
            iteration_start = time.time()
            posts = self._scrape_posts_iteration(profile_urls, posts_per_iteration)
            
            if not posts:
                logger.warning(f"No posts retrieved in iteration {iteration + 1}")
                continue
            
            total_posts_scraped += len(posts)
            
            # Filter out already processed posts
            unprocessed_posts = self.tracker.get_unprocessed_posts(posts)
            logger.info(f"Got {len(posts)} posts, {len(unprocessed_posts)} are new")
            
            if not unprocessed_posts:
                logger.warning(f"No new posts to process in iteration {iteration + 1}")
                continue
            
            # Process the unprocessed posts
            iteration_accepted = self._process_posts_iteration(
                unprocessed_posts,
                content_categories,
                min_quality_score,
                min_category_score,
                min_overall_score
            )
            
            accepted_images.extend(iteration_accepted)
            total_posts_processed += len(unprocessed_posts)
            
            iteration_time = time.time() - iteration_start
            iteration_results.append({
                'iteration': iteration + 1,
                'posts_scraped': len(posts),
                'posts_processed': len(unprocessed_posts),
                'accepted': len(iteration_accepted),
                'time_seconds': iteration_time
            })
            
            logger.info(f"Iteration {iteration + 1} complete: {len(iteration_accepted)} accepted, {iteration_time:.1f}s")
            
            # Brief pause between iterations to be respectful to APIs
            if iteration < max_iterations - 1:
                time.sleep(2)
        
        # Final results
        total_time = time.time() - start_time
        final_accepted_count = len(accepted_images) + len(existing_accepted)
        
        results = {
            'success': final_accepted_count >= target_count,
            'target_count': target_count,
            'accepted_count': final_accepted_count,
            'new_accepted_count': len(accepted_images),
            'existing_accepted_count': len(existing_accepted),
            'total_posts_scraped': total_posts_scraped,
            'total_posts_processed': total_posts_processed,
            'iterations_completed': len(iteration_results),
            'total_time_seconds': total_time,
            'accepted_images': accepted_images,
            'iteration_results': iteration_results,
            'tracker_stats': self.tracker.get_stats()
        }
        
        # Log final summary
        logger.info(f"\n=== BATCH PROCESSING COMPLETE ===")
        logger.info(f"Target: {target_count}, Achieved: {final_accepted_count}")
        logger.info(f"New images: {len(accepted_images)}, Existing: {len(existing_accepted)}")
        logger.info(f"Total posts scraped: {total_posts_scraped}")
        logger.info(f"Total posts processed: {total_posts_processed}")
        logger.info(f"Success rate: {(len(accepted_images) / total_posts_processed * 100) if total_posts_processed > 0 else 0:.1f}%")
        logger.info(f"Total time: {total_time:.1f} seconds")
        
        # Save batch results
        self._save_batch_results(results)
        
        return results
    
    def _scrape_posts_iteration(self, profile_urls: List[str], posts_count: int) -> List[Dict[str, Any]]:
        """Scrape posts for a single iteration."""
        try:
            # Run Instagram scraper
            scraper_run = run_instagram_scraper_for_profiles(
                self.apify_client, 
                profile_urls, 
                posts_count
            )
            
            if not scraper_run or not scraper_run.get('defaultDatasetId'):
                logger.error("Scraping failed or no dataset produced")
                return []
            
            # Get scraped data
            dataset_id = scraper_run['defaultDatasetId']
            posts = get_scraped_data(self.apify_client, dataset_id)
            
            if not posts:
                logger.error("No posts found in scraped data")
                return []
            
            # Filter out video posts
            photo_posts = [post for post in posts if not post.get('isVideo', False)]
            logger.info(f"Filtered {len(posts)} posts to {len(photo_posts)} photo posts")
            
            return photo_posts
            
        except Exception as e:
            logger.error(f"Error in scraping iteration: {e}")
            return []
    
    def _process_posts_iteration(self, 
                                posts: List[Dict[str, Any]],
                                content_categories: List[str],
                                min_quality_score: float,
                                min_category_score: float,
                                min_overall_score: float) -> List[Dict[str, Any]]:
        """Process posts for a single iteration."""
        accepted_images = []
        
        for post in posts:
            try:
                # Download and process the image
                processed_post = self._download_and_analyze_image(
                    post,
                    content_categories,
                    min_quality_score,
                    min_category_score,
                    min_overall_score
                )
                
                if processed_post:
                    if processed_post['status'] == 'accepted':
                        accepted_images.append(processed_post)
                        logger.info(f"✅ Accepted: {processed_post['shortcode']} (score: {processed_post.get('overall_score', 0):.3f})")
                    else:
                        logger.info(f"❌ Rejected: {processed_post['shortcode']} ({processed_post.get('rejection_reason', 'unknown')})")
                
            except Exception as e:
                logger.error(f"Error processing post {post.get('shortCode', 'unknown')}: {e}")
                # Mark as error in tracker
                self.tracker.mark_processed(post, 'error')
        
        return accepted_images
    
    def _download_and_analyze_image(self, 
                                   post: Dict[str, Any],
                                   content_categories: List[str],
                                   min_quality_score: float,
                                   min_category_score: float,
                                   min_overall_score: float) -> Optional[Dict[str, Any]]:
        """Download and analyze a single image."""
        try:
            # Get image URL
            image_url = post.get('displayUrl')
            if not image_url and 'images' in post and post['images']:
                image_url = post['images'][0]
            
            if not image_url:
                logger.warning(f"No image URL for post {post.get('shortCode')}")
                self.tracker.mark_processed(post, 'error')
                return None
            
            # Extract metadata
            post_metadata = extract_post_metadata(post)
            shortcode = post.get('shortCode', f"unknown_{int(time.time())}")
            
            # Generate filename and path
            local_filename = f"{post_metadata['owner_username']}_{shortcode}.jpg"
            
            # Use GCS for storage if available, otherwise local
            if self.use_gcs and self.gcs:
                # Download to temporary local file first
                temp_dir = os.path.join(self.base_dir, 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                local_path = os.path.join(temp_dir, local_filename)
            else:
                # Use local storage
                from ..utils.image_utils import create_storage_structure
                storage_paths = create_storage_structure(self.base_dir)
                local_path = os.path.join(storage_paths['original'], local_filename)
            
            # Download image
            from ..utils.image_utils import download_image, is_landscape, get_image_metadata
            image_data = download_image(image_url, local_path)
            
            if not image_data:
                logger.warning(f"Failed to download image for {shortcode}")
                self.tracker.mark_processed(post, 'error')
                return None
            
            # Check landscape orientation
            landscape = is_landscape(image_data, 1.2)
            if not landscape:
                logger.info(f"Skipping non-landscape image: {shortcode}")
                self.tracker.mark_processed(post, 'rejected', None, local_path)
                if os.path.exists(local_path):
                    os.remove(local_path)
                return {'status': 'rejected', 'shortcode': shortcode, 'rejection_reason': 'not landscape'}
            
            # Enhanced content analysis
            meets_criteria, analysis = self.enhanced_filter.meets_content_criteria(
                image_path=local_path,
                content_categories=content_categories,
                min_quality_score=min_quality_score,
                min_category_score=min_category_score,
                min_overall_score=min_overall_score
            )
            
            # Prepare result
            result = {
                'status': 'accepted' if meets_criteria else 'rejected',
                'shortcode': shortcode,
                'local_path': local_path,
                'post_metadata': post_metadata,
                'analysis': analysis,
                'overall_score': analysis.get('overall_score', 0),
                'quality_score': analysis.get('quality_score', 0),
                'is_video_thumbnail': analysis.get('is_video_thumbnail', False)
            }
            
            if not meets_criteria:
                # Determine rejection reason
                if analysis.get('is_video_thumbnail'):
                    result['rejection_reason'] = 'video thumbnail'
                elif analysis.get('overall_score', 0) < min_overall_score:
                    result['rejection_reason'] = f"overall score {analysis.get('overall_score', 0):.3f} < {min_overall_score}"
                elif analysis.get('quality_score', 0) < min_quality_score:
                    result['rejection_reason'] = f"quality score {analysis.get('quality_score', 0):.3f} < {min_quality_score}"
                else:
                    result['rejection_reason'] = 'category criteria not met'
            
            # Upload to GCS if configured and accepted
            if meets_criteria and self.use_gcs and self.gcs:
                gcs_path = f"images/batch/{local_filename}"
                if self.gcs.upload_file(local_path, gcs_path):
                    result['gcs_path'] = gcs_path
                    logger.info(f"Uploaded to GCS: {gcs_path}")
            
            # Update tracker
            status = 'accepted' if meets_criteria else 'rejected'
            self.tracker.mark_processed(post, status, analysis, local_path)
            
            # Clean up temp file if using GCS
            if self.use_gcs and meets_criteria and os.path.exists(local_path) and 'temp' in local_path:
                os.remove(local_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error downloading/analyzing image: {e}")
            self.tracker.mark_processed(post, 'error')
            return None
    
    def _save_batch_results(self, results: Dict[str, Any]):
        """Save batch processing results to file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = os.path.join(self.base_dir, 'batch_results', f'batch_results_{timestamp}.json')
            
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Batch results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving batch results: {e}")

def test_batch_processor():
    """Test the batch processor."""
    processor = BatchProcessor(base_dir='data', use_gcs=True)
    
    # Test with small batch
    results = processor.process_batch(
        target_count=3,
        max_iterations=2,
        posts_per_iteration=20
    )
    
    print(f"Batch processing results:")
    print(f"  Success: {results['success']}")
    print(f"  Accepted: {results['accepted_count']}/{results['target_count']}")
    print(f"  Time: {results['total_time_seconds']:.1f}s")

if __name__ == "__main__":
    test_batch_processor()
