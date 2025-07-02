#!/usr/bin/env python3
"""
Enhanced Video Detection Module
Detects video thumbnails that may have been misclassified as photos
"""

import os
import cv2
import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoThumbnailDetector:
    """
    Detects if an image is likely a video thumbnail based on visual cues.
    """
    
    def __init__(self):
        """Initialize the video thumbnail detector."""
        self.play_button_templates = self._create_play_button_templates()
        logger.info("Video thumbnail detector initialized")
    
    def _create_play_button_templates(self) -> list:
        """
        Create template images for common play button styles including Instagram video icons.
        
        Returns:
            List of play button template images as numpy arrays.
        """
        templates = []
        
        # Create Instagram video icon templates (top-right corner icon)
        instagram_icon_sizes = [20, 25, 30, 35, 40]
        
        for size in instagram_icon_sizes:
            # Create Instagram video icon template (rounded rectangle with play triangle)
            template = np.zeros((size, size, 3), dtype=np.uint8)
            
            # Draw rounded rectangle background (like Instagram video icon)
            cv2.rectangle(template, (2, 2), (size-2, size-2), (255, 255, 255), -1)
            cv2.rectangle(template, (0, 0), (size, size), (200, 200, 200), 1)
            
            # Draw play triangle in center
            center_x, center_y = size // 2, size // 2
            triangle_size = size // 3
            triangle_points = np.array([
                [center_x - triangle_size//2, center_y - triangle_size//2],
                [center_x - triangle_size//2, center_y + triangle_size//2],
                [center_x + triangle_size//2, center_y]
            ], np.int32)
            
            cv2.fillPoly(template, [triangle_points], (100, 100, 100))
            templates.append(cv2.cvtColor(template, cv2.COLOR_BGR2GRAY))
        
        # Create traditional circular play buttons
        circular_sizes = [30, 40, 50, 60, 80, 100]
        
        for size in circular_sizes:
            # Create circular play button template
            template = np.zeros((size, size, 3), dtype=np.uint8)
            center = (size // 2, size // 2)
            radius = size // 2 - 2
            
            # Draw circle (play button background)
            cv2.circle(template, center, radius, (255, 255, 255), -1)
            cv2.circle(template, center, radius, (200, 200, 200), 2)
            
            # Draw triangle (play symbol)
            triangle_size = radius // 2
            triangle_points = np.array([
                [center[0] - triangle_size//2, center[1] - triangle_size],
                [center[0] - triangle_size//2, center[1] + triangle_size],
                [center[0] + triangle_size, center[1]]
            ], np.int32)
            
            cv2.fillPoly(template, [triangle_points], (100, 100, 100))
            templates.append(cv2.cvtColor(template, cv2.COLOR_BGR2GRAY))
        
        return templates
    
    def detect_play_button(self, image_path: str, threshold: float = 0.6) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Detect if image contains a play button using template matching.
        
        Args:
            image_path: Path to the image file.
            threshold: Confidence threshold for play button detection.
            
        Returns:
            Tuple of (has_play_button, confidence, detection_details)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return False, 0.0, {}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            best_match = 0.0
            best_location = None
            best_template_size = None
            
            # Try each template
            for i, template in enumerate(self.play_button_templates):
                # Template matching
                result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_match:
                    best_match = max_val
                    best_location = max_loc
                    best_template_size = template.shape
            
            # Check if we found a good match
            has_play_button = best_match >= threshold
            
            detection_details = {
                'confidence': float(best_match),
                'location': best_location,
                'template_size': best_template_size,
                'threshold_used': threshold
            }
            
            if has_play_button:
                logger.info(f"Play button detected in {image_path} with confidence {best_match:.3f}")
            
            return has_play_button, best_match, detection_details
            
        except Exception as e:
            logger.error(f"Error detecting play button in {image_path}: {e}")
            return False, 0.0, {}
    
    def detect_instagram_video_icon(self, image_path: str, threshold: float = 0.4) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Specifically detect Instagram video icon in top-right corner.
        
        Args:
            image_path: Path to the image file.
            threshold: Confidence threshold for icon detection.
            
        Returns:
            Tuple of (has_video_icon, confidence, detection_details)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return False, 0.0, {}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Focus on top-right corner (where Instagram video icons appear)
            corner_size = min(width // 4, height // 4, 100)  # Max 100px corner region
            top_right_region = gray[0:corner_size, width-corner_size:width]
            
            best_match = 0.0
            best_location = None
            best_template_size = None
            
            # Try Instagram icon templates (first 5 templates are Instagram-style)
            for i, template in enumerate(self.play_button_templates[:5]):
                if template.shape[0] > corner_size or template.shape[1] > corner_size:
                    continue  # Skip templates that are too large for the corner region
                
                # Template matching in top-right corner
                result = cv2.matchTemplate(top_right_region, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_match:
                    best_match = max_val
                    # Adjust location to full image coordinates
                    best_location = (max_loc[0] + width - corner_size, max_loc[1])
                    best_template_size = template.shape
            
            # Check if we found a good match
            has_video_icon = best_match >= threshold
            
            detection_details = {
                'confidence': float(best_match),
                'location': best_location,
                'template_size': best_template_size,
                'threshold_used': threshold,
                'search_region': f"top-right corner ({corner_size}x{corner_size})"
            }
            
            if has_video_icon:
                logger.info(f"Instagram video icon detected in {image_path} with confidence {best_match:.3f}")
            
            return has_video_icon, best_match, detection_details
            
        except Exception as e:
            logger.error(f"Error detecting Instagram video icon in {image_path}: {e}")
            return False, 0.0, {}
    
    def detect_video_indicators(self, image_path: str) -> Dict[str, Any]:
        """
        Detect various indicators that suggest an image is a video thumbnail.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Dictionary with detection results for various video indicators.
        """
        results = {
            'is_likely_video': False,
            'confidence_score': 0.0,
            'indicators': {}
        }
        
        try:
            # 1. Check filename for video indicators
            filename = os.path.basename(image_path).lower()
            filename_indicators = self._check_filename_indicators(filename)
            results['indicators']['filename'] = filename_indicators
            
            # 2. Check for play button
            has_play_button, play_confidence, play_details = self.detect_play_button(image_path)
            results['indicators']['play_button'] = {
                'detected': has_play_button,
                'confidence': play_confidence,
                'details': play_details
            }
            
            # 3. Check for video UI elements (progress bars, time stamps, etc.)
            ui_indicators = self._detect_video_ui_elements(image_path)
            results['indicators']['ui_elements'] = ui_indicators
            
            # 4. Check aspect ratio (videos often have specific ratios)
            aspect_ratio_info = self._check_aspect_ratio(image_path)
            results['indicators']['aspect_ratio'] = aspect_ratio_info
            
            # 5. Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(results['indicators'])
            results['confidence_score'] = confidence_score
            results['is_likely_video'] = confidence_score > 0.5
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting video indicators in {image_path}: {e}")
            return results
    
    def _check_filename_indicators(self, filename: str) -> Dict[str, Any]:
        """Check filename for video-related indicators."""
        indicators = {
            'has_video_suffix': False,
            'has_video_keywords': False,
            'suspicious_patterns': []
        }
        
        # Check for video suffixes
        video_suffixes = ['_v', '_video', '_vid', '_reel', '_story']
        for suffix in video_suffixes:
            if suffix in filename:
                indicators['has_video_suffix'] = True
                indicators['suspicious_patterns'].append(f"Contains '{suffix}'")
        
        # Check for video keywords
        video_keywords = ['video', 'reel', 'story', 'clip', 'movie']
        for keyword in video_keywords:
            if keyword in filename:
                indicators['has_video_keywords'] = True
                indicators['suspicious_patterns'].append(f"Contains '{keyword}'")
        
        return indicators
    
    def _detect_video_ui_elements(self, image_path: str) -> Dict[str, Any]:
        """Detect video UI elements like progress bars, timestamps, etc."""
        ui_elements = {
            'progress_bar_detected': False,
            'timestamp_detected': False,
            'video_controls_detected': False
        }
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return ui_elements
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Look for horizontal lines in bottom area (progress bars)
            bottom_region = gray[int(height * 0.8):, :]
            
            # Use HoughLines to detect horizontal lines
            edges = cv2.Canny(bottom_region, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=width//4, maxLineGap=10)
            
            if lines is not None:
                horizontal_lines = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Check if line is roughly horizontal
                    if abs(y2 - y1) < 5 and abs(x2 - x1) > width // 6:
                        horizontal_lines.append(line)
                
                if horizontal_lines:
                    ui_elements['progress_bar_detected'] = True
            
            # TODO: Add timestamp detection using OCR
            # TODO: Add video control button detection
            
        except Exception as e:
            logger.error(f"Error detecting UI elements: {e}")
        
        return ui_elements
    
    def _check_aspect_ratio(self, image_path: str) -> Dict[str, Any]:
        """Check if aspect ratio suggests video content."""
        aspect_info = {
            'ratio': 0.0,
            'is_video_ratio': False,
            'ratio_type': 'unknown'
        }
        
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                ratio = width / height
                aspect_info['ratio'] = ratio
                
                # Common video aspect ratios
                video_ratios = {
                    '16:9': (16/9, 0.1),      # Standard widescreen
                    '4:3': (4/3, 0.1),        # Traditional TV
                    '21:9': (21/9, 0.1),      # Ultra-wide
                    '9:16': (9/16, 0.1),      # Vertical video (stories, reels)
                    '1:1': (1.0, 0.1),        # Square (Instagram posts)
                }
                
                for ratio_name, (target_ratio, tolerance) in video_ratios.items():
                    if abs(ratio - target_ratio) <= tolerance:
                        aspect_info['is_video_ratio'] = True
                        aspect_info['ratio_type'] = ratio_name
                        break
                        
        except Exception as e:
            logger.error(f"Error checking aspect ratio: {e}")
        
        return aspect_info
    
    def _calculate_overall_confidence(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall confidence that image is a video thumbnail."""
        confidence = 0.0
        
        # Play button detection (highest weight)
        if indicators.get('play_button', {}).get('detected', False):
            play_conf = indicators['play_button']['confidence']
            confidence += play_conf * 0.6  # 60% weight
        
        # Filename indicators
        filename_info = indicators.get('filename', {})
        if filename_info.get('has_video_suffix', False):
            confidence += 0.3  # 30% weight
        if filename_info.get('has_video_keywords', False):
            confidence += 0.2  # 20% weight
        
        # UI elements
        ui_info = indicators.get('ui_elements', {})
        if ui_info.get('progress_bar_detected', False):
            confidence += 0.25  # 25% weight
        
        # Aspect ratio (lower weight since many photos share video ratios)
        aspect_info = indicators.get('aspect_ratio', {})
        if aspect_info.get('is_video_ratio', False) and aspect_info.get('ratio_type') == '9:16':
            confidence += 0.15  # Vertical videos are more suspicious
        
        # Cap at 1.0
        return min(confidence, 1.0)

def test_video_detection(image_dir: str = "data/raw/original") -> None:
    """Test video detection on images in a directory."""
    detector = VideoThumbnailDetector()
    
    if not os.path.exists(image_dir):
        logger.error(f"Directory not found: {image_dir}")
        return
    
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        logger.error(f"No images found in {image_dir}")
        return
    
    print(f"Testing video detection on {len(image_files)} images")
    print("=" * 80)
    
    results = []
    
    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        
        # Detect video indicators
        detection_results = detector.detect_video_indicators(image_path)
        
        results.append({
            'filename': image_file,
            'is_likely_video': detection_results['is_likely_video'],
            'confidence': detection_results['confidence_score'],
            'indicators': detection_results['indicators']
        })
        
        # Print results
        status = "🎥 LIKELY VIDEO" if detection_results['is_likely_video'] else "📷 LIKELY PHOTO"
        confidence = detection_results['confidence_score']
        
        print(f"{status} | {image_file}")
        print(f"  Confidence: {confidence:.3f}")
        
        # Show specific indicators
        indicators = detection_results['indicators']
        
        if indicators.get('play_button', {}).get('detected', False):
            play_conf = indicators['play_button']['confidence']
            print(f"  ▶️  Play button detected (confidence: {play_conf:.3f})")
        
        filename_info = indicators.get('filename', {})
        if filename_info.get('suspicious_patterns'):
            print(f"  📝 Filename indicators: {', '.join(filename_info['suspicious_patterns'])}")
        
        ui_info = indicators.get('ui_elements', {})
        if ui_info.get('progress_bar_detected'):
            print(f"  📊 Progress bar detected")
        
        aspect_info = indicators.get('aspect_ratio', {})
        if aspect_info.get('is_video_ratio'):
            ratio_type = aspect_info.get('ratio_type', 'unknown')
            print(f"  📐 Video aspect ratio: {ratio_type}")
        
        print()
    
    # Summary
    video_count = sum(1 for r in results if r['is_likely_video'])
    photo_count = len(results) - video_count
    
    print("=" * 80)
    print(f"SUMMARY: {photo_count} photos, {video_count} likely videos out of {len(results)} total")
    
    if video_count > 0:
        print("\nLikely video thumbnails:")
        for result in results:
            if result['is_likely_video']:
                print(f"  - {result['filename']} (confidence: {result['confidence']:.3f})")

if __name__ == "__main__":
    test_video_detection()
