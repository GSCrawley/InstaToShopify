#!/usr/bin/env python3
"""
Test script for the enhanced content filtering system
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from src
from src.phase1_acquisition.enhanced_content_filter import EnhancedContentFilter

def main():
    """Test the enhanced content filter."""
    
    # Test with water/ocean content
    content_categories = ['water', 'landscape', 'sunset', 'nature']
    
    filter_system = EnhancedContentFilter()
    
    image_dir = "data/raw/original"
    
    if not os.path.exists(image_dir):
        print(f"Directory not found: {image_dir}")
        return
    
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"No images found in {image_dir}")
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
            content_categories=content_categories,
            min_quality_score=0.3,  # Lower thresholds for testing
            min_category_score=0.3,
            min_overall_score=0.4
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
    main()
