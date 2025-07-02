#!/usr/bin/env python3
"""
Image Tracking System

Tracks processed images to avoid reprocessing the same content.
Maintains a database of processed Instagram posts and their status.
"""

import os
import json
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class ImageTracker:
    """
    Tracks processed Instagram images to avoid duplicates and enable batch processing.
    """
    
    def __init__(self, base_dir: str = 'data'):
        """
        Initialize the image tracker.
        
        Args:
            base_dir: Base directory for storing tracking data
        """
        self.base_dir = base_dir
        self.tracking_dir = os.path.join(base_dir, 'tracking')
        self.tracking_file = os.path.join(self.tracking_dir, 'processed_images.json')
        
        # Ensure tracking directory exists
        os.makedirs(self.tracking_dir, exist_ok=True)
        
        # Load existing tracking data
        self.processed_images = self._load_tracking_data()
        
        logger.info(f"Image tracker initialized. Tracking {len(self.processed_images)} processed images.")
    
    def _load_tracking_data(self) -> Dict[str, Dict]:
        """Load existing tracking data from file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded tracking data for {len(data)} images")
                return data
            except Exception as e:
                logger.error(f"Error loading tracking data: {e}")
                return {}
        return {}
    
    def _save_tracking_data(self):
        """Save tracking data to file."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.processed_images, f, indent=2)
            logger.debug(f"Saved tracking data for {len(self.processed_images)} images")
        except Exception as e:
            logger.error(f"Error saving tracking data: {e}")
    
    def _generate_image_id(self, post_data: Dict) -> str:
        """
        Generate a unique ID for an Instagram post.
        
        Args:
            post_data: Instagram post data from Apify
            
        Returns:
            Unique identifier for the post
        """
        # Use shortcode as primary identifier
        shortcode = post_data.get('shortCode')
        if shortcode:
            return shortcode
        
        # Fallback to post ID
        post_id = post_data.get('id')
        if post_id:
            return post_id
        
        # Last resort: hash of image URL
        image_url = post_data.get('displayUrl') or (post_data.get('images', [{}])[0] if post_data.get('images') else '')
        if image_url:
            return hashlib.md5(image_url.encode()).hexdigest()[:12]
        
        # Should not happen, but just in case
        return f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def is_processed(self, post_data: Dict) -> bool:
        """
        Check if an Instagram post has already been processed.
        
        Args:
            post_data: Instagram post data from Apify
            
        Returns:
            True if the post has been processed, False otherwise
        """
        image_id = self._generate_image_id(post_data)
        return image_id in self.processed_images
    
    def mark_processed(self, post_data: Dict, status: str, analysis_results: Dict = None, local_path: str = None):
        """
        Mark an Instagram post as processed.
        
        Args:
            post_data: Instagram post data from Apify
            status: Processing status ('accepted', 'rejected', 'error')
            analysis_results: Results from enhanced content filter analysis
            local_path: Local path to downloaded image (if applicable)
        """
        image_id = self._generate_image_id(post_data)
        
        tracking_entry = {
            'image_id': image_id,
            'shortcode': post_data.get('shortCode'),
            'post_id': post_data.get('id'),
            'owner_username': post_data.get('ownerUsername'),
            'timestamp': post_data.get('timestamp'),
            'url': post_data.get('url'),
            'status': status,
            'processed_at': datetime.now().isoformat(),
            'local_path': local_path
        }
        
        # Add analysis results if provided
        if analysis_results:
            tracking_entry['analysis'] = {
                'overall_score': analysis_results.get('overall_score', 0),
                'quality_score': analysis_results.get('quality_score', 0),
                'is_video_thumbnail': analysis_results.get('is_video_thumbnail', False),
                'category_matches': analysis_results.get('category_matches', {})
            }
        
        self.processed_images[image_id] = tracking_entry
        self._save_tracking_data()
        
        logger.debug(f"Marked image {image_id} as {status}")
    
    def get_processed_count(self, status: str = None) -> int:
        """
        Get count of processed images.
        
        Args:
            status: Filter by status ('accepted', 'rejected', 'error'). None for all.
            
        Returns:
            Count of processed images
        """
        if status is None:
            return len(self.processed_images)
        
        return sum(1 for entry in self.processed_images.values() if entry.get('status') == status)
    
    def get_accepted_images(self) -> List[Dict]:
        """
        Get list of accepted images.
        
        Returns:
            List of tracking entries for accepted images
        """
        return [entry for entry in self.processed_images.values() if entry.get('status') == 'accepted']
    
    def get_unprocessed_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Filter out already processed posts from a list.
        
        Args:
            posts: List of Instagram post data from Apify
            
        Returns:
            List of unprocessed posts
        """
        unprocessed = []
        for post in posts:
            if not self.is_processed(post):
                unprocessed.append(post)
            else:
                image_id = self._generate_image_id(post)
                logger.debug(f"Skipping already processed image: {image_id}")
        
        logger.info(f"Filtered {len(posts)} posts to {len(unprocessed)} unprocessed posts")
        return unprocessed
    
    def cleanup_old_entries(self, days: int = 30):
        """
        Remove tracking entries older than specified days.
        
        Args:
            days: Number of days to keep entries
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_entries = []
        for image_id, entry in self.processed_images.items():
            try:
                processed_at = datetime.fromisoformat(entry.get('processed_at', ''))
                if processed_at < cutoff_date:
                    old_entries.append(image_id)
            except ValueError:
                # Invalid date format, consider it old
                old_entries.append(image_id)
        
        for image_id in old_entries:
            del self.processed_images[image_id]
        
        if old_entries:
            self._save_tracking_data()
            logger.info(f"Cleaned up {len(old_entries)} old tracking entries")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about processed images.
        
        Returns:
            Dictionary with processing statistics
        """
        total = len(self.processed_images)
        accepted = self.get_processed_count('accepted')
        rejected = self.get_processed_count('rejected')
        errors = self.get_processed_count('error')
        
        return {
            'total_processed': total,
            'accepted': accepted,
            'rejected': rejected,
            'errors': errors,
            'acceptance_rate': (accepted / total * 100) if total > 0 else 0
        }
    
    def reset_tracking(self):
        """Reset all tracking data. Use with caution!"""
        self.processed_images = {}
        self._save_tracking_data()
        logger.warning("All tracking data has been reset")

def test_image_tracker():
    """Test the image tracker functionality."""
    tracker = ImageTracker(base_dir='data')
    
    # Test data
    test_post = {
        'shortCode': 'test123',
        'id': '12345',
        'ownerUsername': 'testuser',
        'timestamp': '2023-01-01T00:00:00Z',
        'url': 'https://instagram.com/p/test123/',
        'displayUrl': 'https://example.com/image.jpg'
    }
    
    # Test processing
    print(f"Is processed (before): {tracker.is_processed(test_post)}")
    
    tracker.mark_processed(test_post, 'accepted', {'overall_score': 0.8}, '/path/to/image.jpg')
    
    print(f"Is processed (after): {tracker.is_processed(test_post)}")
    print(f"Stats: {tracker.get_stats()}")

if __name__ == "__main__":
    test_image_tracker()
