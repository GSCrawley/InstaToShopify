def test_quality_routing():
    """Test quality-based routing with different scores"""
    from src.phase3_multi_tier_fulfillment.quality_router import QualityBasedRouter
    
    router = QualityBasedRouter()
    
    test_cases = [
        {'score': 0.95, 'expected_tier': 'premium'},
        {'score': 0.80, 'expected_tier': 'professional'},
        {'score': 0.65, 'expected_tier': 'canvas'},
        {'score': 0.45, 'expected_result': 'rejected'}
    ]
    
    for case in test_cases:
        test_data = {'enhanced_score': case['score']}
        result = router.route_image(test_data)
        print(f"Score {case['score']}: {result}")