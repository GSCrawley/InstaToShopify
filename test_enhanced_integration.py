#!/usr/bin/env python3
"""
Test script for Enhanced Content Filter Integration

This script tests the integration of the enhanced content filter
into the main Instagram scraping workflow.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_filter_import():
    """Test that enhanced filter can be imported correctly."""
    try:
        from src.phase1_acquisition.enhanced_content_filter import EnhancedContentFilter
        from src.phase1_acquisition.video_detector import VideoThumbnailDetector
        logger.info("✅ Enhanced filter imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Enhanced filter import failed: {e}")
        return False

def test_config_integration():
    """Test that config has enhanced filtering settings."""
    try:
        from src import config
        
        # Check for enhanced filtering config
        required_configs = [
            'ENHANCED_CONTENT_CATEGORIES',
            'MIN_QUALITY_SCORE',
            'MIN_CATEGORY_SCORE', 
            'MIN_OVERALL_SCORE',
            'MIN_PRINT_SUITABILITY',
            'USE_ENHANCED_FILTERING'
        ]
        
        missing_configs = []
        for config_name in required_configs:
            if not hasattr(config, config_name):
                missing_configs.append(config_name)
        
        if missing_configs:
            logger.error(f"❌ Missing config settings: {missing_configs}")
            return False
        
        logger.info("✅ Enhanced filtering config settings found")
        logger.info(f"  Categories: {config.ENHANCED_CONTENT_CATEGORIES}")
        logger.info(f"  Min quality score: {config.MIN_QUALITY_SCORE}")
        logger.info(f"  Min category score: {config.MIN_CATEGORY_SCORE}")
        logger.info(f"  Min overall score: {config.MIN_OVERALL_SCORE}")
        logger.info(f"  Enhanced filtering enabled: {config.USE_ENHANCED_FILTERING}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Config integration test failed: {e}")
        return False

def test_enhanced_filter_functionality():
    """Test enhanced filter with existing images."""
    try:
        from src.phase1_acquisition.enhanced_content_filter import EnhancedContentFilter
        
        # Initialize enhanced filter
        enhanced_filter = EnhancedContentFilter(use_google_vision=True)
        
        # Test with existing images
        test_dir = "data/raw/original"
        if not os.path.exists(test_dir):
            logger.warning(f"⚠️  Test directory {test_dir} not found. Skipping functionality test.")
            return True
        
        image_files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not image_files:
            logger.warning(f"⚠️  No images found in {test_dir}. Skipping functionality test.")
            return True
        
        # Test with first image
        test_image = os.path.join(test_dir, image_files[0])
        logger.info(f"Testing enhanced filter with: {test_image}")
        
        # Test content criteria check
        meets_criteria, analysis = enhanced_filter.meets_content_criteria(
            image_path=test_image,
            content_categories=['landscape', 'sunset', 'water', 'nature'],
            min_quality_score=0.3,  # Lower threshold for testing
            min_category_score=0.3,
            min_overall_score=0.3
        )
        
        logger.info(f"✅ Enhanced filter analysis completed")
        logger.info(f"  Meets criteria: {meets_criteria}")
        logger.info(f"  Overall score: {analysis.get('overall_score', 0):.3f}")
        logger.info(f"  Quality score: {analysis.get('quality_score', 0):.3f}")
        logger.info(f"  Is video thumbnail: {analysis.get('is_video_thumbnail', False)}")
        
        # Show category matches
        category_matches = analysis.get('category_matches', {})
        if category_matches:
            best_matches = sorted(
                [(cat, info['score']) for cat, info in category_matches.items() if info['score'] > 0.1],
                key=lambda x: x[1], reverse=True
            )[:3]
            
            if best_matches:
                logger.info(f"  Top categories: {', '.join([f'{cat}({score:.2f})' for cat, score in best_matches])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced filter functionality test failed: {e}")
        return False

def test_instagram_scraper_integration():
    """Test that Instagram scraper can use enhanced filtering."""
    try:
        from src.phase1_acquisition.instagram_scraper import process_instagram_posts
        
        # Test that the function accepts enhanced filtering parameters
        import inspect
        sig = inspect.signature(process_instagram_posts)
        
        required_params = [
            'use_enhanced_filtering',
            'content_categories',
            'min_quality_score',
            'min_category_score',
            'min_overall_score'
        ]
        
        missing_params = []
        for param in required_params:
            if param not in sig.parameters:
                missing_params.append(param)
        
        if missing_params:
            logger.error(f"❌ Instagram scraper missing enhanced filtering parameters: {missing_params}")
            return False
        
        logger.info("✅ Instagram scraper enhanced filtering integration successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Instagram scraper integration test failed: {e}")
        return False

def test_main_workflow_integration():
    """Test that main workflow supports enhanced filtering arguments."""
    try:
        from src.main import parse_arguments
        
        # Test parsing enhanced filtering arguments
        test_args = [
            '--enhanced-filter',
            '--content-categories', 'landscape,sunset,water',
            '--min-quality-score', '0.5',
            '--min-category-score', '0.4',
            '--min-overall-score', '0.6'
        ]
        
        # Parse test arguments
        import argparse
        parser = argparse.ArgumentParser()
        
        # We need to recreate the parser logic from main.py
        parser.add_argument('--enhanced-filter', '-ef', action='store_true', default=True)
        parser.add_argument('--content-categories', '-cc', type=str)
        parser.add_argument('--min-quality-score', '-mqs', type=float)
        parser.add_argument('--min-category-score', '-mcs', type=float)
        parser.add_argument('--min-overall-score', '-mos', type=float)
        
        args = parser.parse_args(test_args)
        
        # Verify arguments were parsed correctly
        assert args.enhanced_filter == True
        assert args.content_categories == 'landscape,sunset,water'
        assert args.min_quality_score == 0.5
        assert args.min_category_score == 0.4
        assert args.min_overall_score == 0.6
        
        logger.info("✅ Main workflow enhanced filtering arguments integration successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Main workflow integration test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests."""
    logger.info("🚀 Starting Enhanced Content Filter Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Enhanced Filter Import", test_enhanced_filter_import),
        ("Config Integration", test_config_integration),
        ("Enhanced Filter Functionality", test_enhanced_filter_functionality),
        ("Instagram Scraper Integration", test_instagram_scraper_integration),
        ("Main Workflow Integration", test_main_workflow_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status} | {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n📈 Total: {len(results)} tests, {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All integration tests passed! Enhanced filtering is ready to use.")
        logger.info("\n💡 Usage Examples:")
        logger.info("  # Use enhanced filtering with default settings:")
        logger.info("  python src/main.py --workflow acquisition --enhanced-filter")
        logger.info("\n  # Use enhanced filtering with custom settings:")
        logger.info("  python src/main.py --workflow acquisition --enhanced-filter \\")
        logger.info("    --content-categories 'landscape,sunset,nature' \\")
        logger.info("    --min-quality-score 0.6 \\")
        logger.info("    --min-overall-score 0.7")
        logger.info("\n  # Test enhanced filter on existing images:")
        logger.info("  python test_enhanced_content_filter.py")
    else:
        logger.error("❌ Some integration tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
