# src/phase3_multi_tier_fulfillment/creativehub_integration/product_creator.py
from typing import Dict, List
from .api_client import CreativeHubClient
import os
import json

class CreativeHubProductCreator:
    def __init__(self, use_sandbox: bool = False):
        self.client = CreativeHubClient(use_sandbox)
        
    def create_premium_product(self, image_data: Dict) -> Dict:
        """Create a premium fine art product on CreativeHub"""
        try:
            # Prepare metadata
            metadata = self._generate_premium_metadata(image_data)
            
            # Upload image
            upload_result = self.client.upload_image(
                image_data['processed_path'],
                metadata
            )
            
            if upload_result.get('success'):
                product_id = upload_result['Id']
                
                # Get product details with print options
                product_details = self.client.get_product(product_id)
                
                # Configure pricing based on print options
                pricing_config = self._configure_premium_pricing(product_details)
                
                return {
                    'success': True,
                    'platform': 'creativehub',
                    'product_id': product_id,
                    'product_details': product_details,
                    'pricing': pricing_config,
                    'metadata': metadata
                }
            else:
                raise Exception(f"Upload failed: {upload_result.get('error')}")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'creativehub'
            }
    
    def _generate_premium_metadata(self, image_data: Dict) -> Dict:
        """Generate SEO-optimized metadata for premium products"""
        instagram_data = image_data.get('instagram_metadata', {})
        cv_analysis = image_data.get('cv_analysis', {})
        
        # Extract location and mood from hashtags and CV analysis
        location = self._extract_location(instagram_data.get('hashtags', []))
        mood = self._extract_mood(cv_analysis)
        colors = cv_analysis.get('dominant_colors', [])
        
        title = f"{location} Landscape Photography - Fine Art Print"
        if mood:
            title = f"{mood} {title}"
            
        description = f"""
Professional fine art print captured in {location}. This {mood.lower()} landscape 
showcases {', '.join(colors[:3])} tones and is printed on museum-quality paper 
using archival pigment inks. Perfect for collectors and interior design.

- Museum-quality Hahnemühle paper
- Archival pigment inks (100+ year lifespan)  
- Limited edition fine art print
- Certificate of authenticity included
- Ready for framing or mounting
        """.strip()
        
        return {
            'title': title,
            'description': description,
            'artist_name': 'Instagram Fine Art Photography',
            'location': location,
            'mood': mood,
            'colors': colors,
            'hashtags': instagram_data.get('hashtags', [])
        }
    
    def _configure_premium_pricing(self, product_details: Dict) -> Dict:
        """Configure premium pricing strategy"""
        print_options = product_details.get('PrintOptions', [])
        pricing = {}
        
        # Premium markup strategy (300-400%)
        for option in print_options:
            cost = option.get('CostPerItem', 0)
            size = option.get('ShortDescription', 'Unknown')
            
            # Premium pricing based on size and quality
            if 'A4' in size or '8x10' in size:
                retail_price = cost * 4.0  # 400% markup
            elif 'A3' in size or '11x14' in size:
                retail_price = cost * 3.5  # 350% markup
            elif 'A2' in size or '16x20' in size:
                retail_price = cost * 3.0  # 300% markup
            else:
                retail_price = cost * 3.5  # Default premium markup
            
            pricing[option['Id']] = {
                'cost': cost,
                'retail_price': round(retail_price, 2),
                'markup_percentage': round(((retail_price - cost) / cost) * 100, 1),
                'size': size,
                'description': option.get('FullDescription', '')
            }
        
        return pricing
    
    def _extract_location(self, hashtags: List[str]) -> str:
        """Extract location from hashtags"""
        location_keywords = ['landscape', 'mountains', 'ocean', 'forest', 'desert', 'city']
        for tag in hashtags:
            if any(keyword in tag.lower() for keyword in location_keywords):
                return tag.replace('#', '').title()
        return 'Scenic'
    
    def _extract_mood(self, cv_analysis: Dict) -> str:
        """Extract mood from computer vision analysis"""
        # This would integrate with your existing CV analysis
        confidence = cv_analysis.get('quality_score', 0.5)
        if confidence > 0.9:
            return 'Breathtaking'
        elif confidence > 0.85:
            return 'Stunning'
        else:
            return 'Beautiful'