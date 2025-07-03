# Test script for CreativeHub sandbox
def test_creativehub_sandbox():
    """Test CreativeHub integration in sandbox mode"""
    from src.phase3_multi_tier_fulfillment.creativehub_integration.product_creator import CreativeHubProductCreator
    
    # Use sandbox mode
    creator = CreativeHubProductCreator(use_sandbox=True)
    
    # Test with sample image data
    test_image_data = {
        'processed_path': 'test_images/sample_landscape.jpg',
        'enhanced_score': 0.89,
        'instagram_metadata': {
            'hashtags': ['#landscape', '#mountains', '#photography'],
            'caption': 'Beautiful mountain landscape at sunset'
        },
        'cv_analysis': {
            'quality_score': 0.89,
            'dominant_colors': ['blue', 'orange', 'purple']
        }
    }
    
    result = creator.create_premium_product(test_image_data)
    print(f"Sandbox test result: {result}")
    
    return result.get('success', False)