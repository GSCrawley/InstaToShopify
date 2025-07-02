#!/usr/bin/env python3
"""
Enhanced Content Filtering System
Combines Google Vision API with intelligent category matching and quality assessment
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np
import json

# Google Vision API imports
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

from .video_detector import VideoThumbnailDetector

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedContentFilter:
    """
    Enhanced content filtering with intelligent category matching and quality assessment.
    """
    
    def __init__(self, use_google_vision: bool = True, credentials_path: str = None):
        """
        Initialize the enhanced content filter.
        
        Args:
            use_google_vision: Whether to use Google Vision API.
            credentials_path: Path to Google Cloud credentials file.
        """
        self.use_google_vision = use_google_vision and GOOGLE_VISION_AVAILABLE
        self.vision_client = None
        self.video_detector = VideoThumbnailDetector()
        
        # Initialize Google Vision client
        if self.use_google_vision:
            try:
                if credentials_path and os.path.exists(credentials_path):
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                else:
                    logger.warning("No Google Cloud credentials found. Vision API disabled.")
                    self.use_google_vision = False
                    
                if self.vision_client:
                    logger.info("Google Vision API client initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Google Vision API: {e}")
                self.use_google_vision = False
        
        # Enhanced photography categories with semantic understanding
        self.photography_categories = {
            'landscape': {
                'primary_keywords': ['landscape', 'mountain', 'valley', 'horizon', 'countryside', 'scenic', 'vista', 'panorama'],
                'secondary_keywords': ['nature', 'outdoor', 'field', 'hill', 'meadow', 'plain', 'terrain'],
                'related_objects': ['tree', 'rock', 'grass', 'sky', 'cloud'],
                'weight': 1.0
            },
            'sunset': {
                'primary_keywords': ['sunset', 'sunrise', 'golden hour', 'dusk', 'dawn', 'twilight'],
                'secondary_keywords': ['orange', 'golden', 'warm light', 'evening', 'morning'],
                'related_objects': ['sun', 'sky', 'cloud', 'horizon'],
                'weight': 1.0
            },
            'water': {
                'primary_keywords': ['ocean', 'sea', 'lake', 'river', 'waterfall', 'stream', 'water', 'beach', 'coast'],
                'secondary_keywords': ['wave', 'shore', 'coastal', 'marine', 'aquatic', 'fluid'],
                'related_objects': ['boat', 'fish', 'sand', 'rock'],
                'weight': 1.0
            },
            'urban': {
                'primary_keywords': ['city', 'urban', 'building', 'architecture', 'street', 'downtown'],
                'secondary_keywords': ['metropolitan', 'skyscraper', 'cityscape', 'modern'],
                'related_objects': ['car', 'person', 'window', 'door', 'sign'],
                'weight': 0.8
            },
            'nature': {
                'primary_keywords': ['nature', 'forest', 'tree', 'flower', 'plant', 'wildlife', 'animal'],
                'secondary_keywords': ['natural', 'organic', 'botanical', 'flora', 'fauna'],
                'related_objects': ['leaf', 'branch', 'bird', 'insect'],
                'weight': 0.9
            },
            'mountains': {
                'primary_keywords': ['mountain', 'peak', 'summit', 'alpine', 'ridge', 'cliff'],
                'secondary_keywords': ['rocky', 'steep', 'elevation', 'highland'],
                'related_objects': ['snow', 'rock', 'tree', 'sky'],
                'weight': 1.0
            }
        }
        
        logger.info(f"Enhanced content filter initialized. Google Vision: {self.use_google_vision}")
    
    def analyze_image_content(self, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive image content analysis.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Dictionary with comprehensive analysis results.
        """
        analysis = {
            'image_path': image_path,
            'is_video_thumbnail': False,
            'video_confidence': 0.0,
            'google_vision_labels': [],
            'google_vision_objects': [],
            'category_matches': {},
            'quality_score': 0.0,
            'print_suitability': 0.0,
            'overall_score': 0.0
        }
        
        try:
            # 1. Check if it's a video thumbnail
            video_results = self.video_detector.detect_video_indicators(image_path)
            analysis['is_video_thumbnail'] = video_results['is_likely_video']
            analysis['video_confidence'] = video_results['confidence_score']
            analysis['video_indicators'] = video_results['indicators']
            
            # Skip further analysis if it's a video thumbnail
            if analysis['is_video_thumbnail']:
                logger.info(f"Skipping content analysis for video thumbnail: {image_path}")
                return analysis
            
            # 2. Google Vision API analysis
            if self.use_google_vision and self.vision_client:
                vision_results = self._analyze_with_google_vision(image_path)
                analysis['google_vision_labels'] = vision_results.get('labels', [])
                analysis['google_vision_objects'] = vision_results.get('objects', [])
                analysis['google_vision_colors'] = vision_results.get('colors', [])
            
            # 3. Category matching
            analysis['category_matches'] = self._match_categories(analysis)
            
            # 4. Quality assessment
            analysis['quality_score'] = self._assess_image_quality(image_path)
            
            # 5. Print suitability
            analysis['print_suitability'] = self._assess_print_suitability(image_path, analysis)
            
            # 6. Calculate overall score
            analysis['overall_score'] = self._calculate_overall_score(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing image content for {image_path}: {e}")
            return analysis
    
    def _analyze_with_google_vision(self, image_path: str) -> Dict[str, Any]:
        """Analyze image with Google Vision API."""
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Request multiple features
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=20),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10),
                vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
            ]
            
            response = self.vision_client.annotate_image({
                'image': image,
                'features': features
            })
            
            results = {}
            
            # Extract labels
            if response.label_annotations:
                results['labels'] = [
                    {
                        'description': label.description.lower(),
                        'score': label.score,
                        'topicality': label.topicality
                    }
                    for label in response.label_annotations
                ]
            
            # Extract objects
            if response.localized_object_annotations:
                results['objects'] = [
                    {
                        'name': obj.name.lower(),
                        'score': obj.score
                    }
                    for obj in response.localized_object_annotations
                ]
            
            # Extract colors
            if response.image_properties_annotation:
                results['colors'] = [
                    {
                        'color': {
                            'red': color.color.red,
                            'green': color.color.green,
                            'blue': color.color.blue
                        },
                        'score': color.score,
                        'pixel_fraction': color.pixel_fraction
                    }
                    for color in response.image_properties_annotation.dominant_colors.colors[:5]
                ]
            
            return results
            
        except Exception as e:
            logger.error(f"Error with Google Vision analysis: {e}")
            return {}
    
    def _match_categories(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent category matching using semantic understanding.
        """
        category_scores = {}
        
        # Get all detected labels and objects
        all_labels = []
        
        # Add Google Vision labels
        for label in analysis.get('google_vision_labels', []):
            all_labels.append({
                'text': label['description'],
                'confidence': label['score'],
                'source': 'google_vision_label'
            })
        
        # Add Google Vision objects
        for obj in analysis.get('google_vision_objects', []):
            all_labels.append({
                'text': obj['name'],
                'confidence': obj['score'],
                'source': 'google_vision_object'
            })
        
        # Match against photography categories
        for category_name, category_info in self.photography_categories.items():
            score = 0.0
            matches = []
            
            for label in all_labels:
                label_text = label['text'].lower()
                label_confidence = label['confidence']
                
                # Check primary keywords (high weight)
                for keyword in category_info['primary_keywords']:
                    if keyword in label_text or label_text in keyword:
                        match_score = label_confidence * 1.0
                        score += match_score
                        matches.append({
                            'keyword': keyword,
                            'label': label_text,
                            'score': match_score,
                            'type': 'primary'
                        })
                
                # Check secondary keywords (medium weight)
                for keyword in category_info['secondary_keywords']:
                    if keyword in label_text or label_text in keyword:
                        match_score = label_confidence * 0.6
                        score += match_score
                        matches.append({
                            'keyword': keyword,
                            'label': label_text,
                            'score': match_score,
                            'type': 'secondary'
                        })
                
                # Check related objects (lower weight)
                for keyword in category_info['related_objects']:
                    if keyword in label_text or label_text in keyword:
                        match_score = label_confidence * 0.3
                        score += match_score
                        matches.append({
                            'keyword': keyword,
                            'label': label_text,
                            'score': match_score,
                            'type': 'related'
                        })
            
            # Apply category weight
            final_score = score * category_info['weight']
            
            category_scores[category_name] = {
                'score': final_score,
                'matches': matches,
                'match_count': len(matches)
            }
        
        return category_scores
    
    def _assess_image_quality(self, image_path: str) -> float:
        """
        Assess technical image quality.
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Basic quality factors
                resolution_score = min(1.0, (width * height) / (1920 * 1080))  # Normalize to 1080p
                aspect_ratio = width / height
                aspect_score = 1.0 if 0.5 <= aspect_ratio <= 2.0 else 0.5  # Prefer reasonable ratios
                
                # Size score (prefer larger images for print)
                min_dimension = min(width, height)
                size_score = min(1.0, min_dimension / 1200)  # Prefer at least 1200px on shortest side
                
                # Combine scores
                quality_score = (resolution_score * 0.4 + aspect_score * 0.3 + size_score * 0.3)
                
                return quality_score
                
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return 0.0
    
    def _assess_print_suitability(self, image_path: str, analysis: Dict[str, Any]) -> float:
        """
        Assess suitability for printing as wall art.
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Print resolution requirements
                min_dpi = 150  # Minimum for decent print quality
                max_print_width = width / min_dpi  # Max print width in inches
                max_print_height = height / min_dpi
                
                # Score based on maximum printable size
                max_print_size = max(max_print_width, max_print_height)
                print_size_score = min(1.0, max_print_size / 24)  # Prefer images that can print at 24+ inches
                
                # Aspect ratio suitability for wall art
                aspect_ratio = width / height
                if 0.7 <= aspect_ratio <= 1.5:  # Square to moderate landscape/portrait
                    aspect_suitability = 1.0
                elif 0.5 <= aspect_ratio <= 2.0:  # Wider range but lower score
                    aspect_suitability = 0.8
                else:
                    aspect_suitability = 0.5
                
                # Content suitability (based on category matches)
                content_suitability = 0.0
                category_matches = analysis.get('category_matches', {})
                for category, match_info in category_matches.items():
                    if match_info['score'] > 0.5:  # Strong category match
                        content_suitability = max(content_suitability, match_info['score'])
                
                # Combine factors
                print_suitability = (
                    print_size_score * 0.4 +
                    aspect_suitability * 0.3 +
                    content_suitability * 0.3
                )
                
                return print_suitability
                
        except Exception as e:
            logger.error(f"Error assessing print suitability: {e}")
            return 0.0
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate overall score for the image.
        """
        # If it's a video thumbnail, score is 0
        if analysis.get('is_video_thumbnail', False):
            return 0.0
        
        quality_score = analysis.get('quality_score', 0.0)
        print_suitability = analysis.get('print_suitability', 0.0)
        
        # Get best category match score
        best_category_score = 0.0
        category_matches = analysis.get('category_matches', {})
        for category, match_info in category_matches.items():
            best_category_score = max(best_category_score, match_info['score'])
        
        # Normalize category score
        normalized_category_score = min(1.0, best_category_score / 2.0)
        
        # Weighted combination
        overall_score = (
            quality_score * 0.3 +
            print_suitability * 0.4 +
            normalized_category_score * 0.3
        )
        
        return overall_score
    
    def meets_content_criteria(self, image_path: str, 
                              content_categories: List[str] = None,
                              min_quality_score: float = 0.5,
                              min_category_score: float = 0.5,
                              min_overall_score: float = 0.6) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if image meets content criteria.
        
        Args:
            image_path: Path to the image.
            content_categories: List of desired content categories.
            min_quality_score: Minimum quality score required.
            min_category_score: Minimum category match score required.
            min_overall_score: Minimum overall score required.
            
        Returns:
            Tuple of (meets_criteria, analysis_results)
        """
        analysis = self.analyze_image_content(image_path)
        
        # Reject video thumbnails immediately
        if analysis.get('is_video_thumbnail', False):
            return False, analysis
        
        # Check quality score
        if analysis.get('quality_score', 0.0) < min_quality_score:
            return False, analysis
        
        # Check category matching if categories specified
        if content_categories:
            best_match_score = 0.0
            for category in content_categories:
                if category in analysis.get('category_matches', {}):
                    category_score = analysis['category_matches'][category]['score']
                    best_match_score = max(best_match_score, category_score)
            
            if best_match_score < min_category_score:
                return False, analysis
        
        # Check overall score
        if analysis.get('overall_score', 0.0) < min_overall_score:
            return False, analysis
        
        return True, analysis

def test_enhanced_filter(image_dir: str = "data/raw/original", 
                        content_categories: List[str] = None) -> None:
    """Test the enhanced content filter."""
    
    if content_categories is None:
        content_categories = ['landscape', 'sunset', 'water', 'nature']
    
    filter_system = EnhancedContentFilter()
    
    if not os.path.exists(image_dir):
        logger.error(f"Directory not found: {image_dir}")
        return
    
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        logger.error(f"No images found in {image_dir}")
        return
    
    print(f"Testing enhanced content filter on {len(image_files)} images")
    print(f"Looking for categories: {content_categories}")
    print("=" * 80)
    
    results = []
    
    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        
        # Analyze image
        meets_criteria, analysis = filter_system.meets_content_criteria(
            image_path, 
            content_categories=content_categories
        )
        
        results.append({
            'filename': image_file,
            'meets_criteria': meets_criteria,
            'analysis': analysis
        })
        
        # Print results
        status = "✅ ACCEPTED" if meets_criteria else "❌ REJECTED"
        print(f"{status} | {image_file}")
        
        if analysis.get('is_video_thumbnail'):
            print(f"  🎥 Video thumbnail detected (confidence: {analysis.get('video_confidence', 0):.3f})")
        else:
            print(f"  📊 Quality: {analysis.get('quality_score', 0):.3f}")
            print(f"  🖼️  Print suitability: {analysis.get('print_suitability', 0):.3f}")
            print(f"  ⭐ Overall score: {analysis.get('overall_score', 0):.3f}")
            
            # Show best category matches
            category_matches = analysis.get('category_matches', {})
            best_matches = sorted(
                [(cat, info['score']) for cat, info in category_matches.items() if info['score'] > 0.1],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            if best_matches:
                print(f"  🏷️  Top categories: {', '.join([f'{cat}({score:.2f})' for cat, score in best_matches])}")
        
        print()
    
    # Summary
    accepted_count = sum(1 for r in results if r['meets_criteria'])
    rejected_count = len(results) - accepted_count
    
    print("=" * 80)
    print(f"SUMMARY: {accepted_count} accepted, {rejected_count} rejected out of {len(results)} total")
    
    if accepted_count > 0:
        print("\nAccepted images:")
        for result in results:
            if result['meets_criteria']:
                analysis = result['analysis']
                print(f"  - {result['filename']} (score: {analysis.get('overall_score', 0):.3f})")

if __name__ == "__main__":
    test_enhanced_filter()
