from flask import Flask, request, jsonify
import hmac
import hashlib
import base64
import json
from typing import Dict
from config import PrintStrategy
from .order_router import ShopifyOrderRouter

app = Flask(__name__)
order_router = ShopifyOrderRouter()

def verify_webhook(data: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook authenticity"""
    computed_hmac = base64.b64encode(
        hmac.new(
            PrintStrategy.SHOPIFY_WEBHOOK_SECRET.encode('utf-8'),
            data,
            digestmod=hashlib.sha256
        ).digest()
    )
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

@app.route('/webhooks/shopify/orders/create', methods=['POST'])
def handle_order_created():
    """Handle new Shopify order webhook"""
    try:
        # Verify webhook authenticity
        hmac_header = request.headers.get('X-Shopify-Hmac-Sha256')
        if not verify_webhook(request.get_data(), hmac_header):
            return jsonify({'error': 'Invalid webhook signature'}), 401
        
        order_data = request.get_json()
        
        # Route order to appropriate fulfillment platform(s)
        routing_result = order_router.route_order(order_data)
        
        if routing_result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Order routed for fulfillment',
                'order_id': routing_result['order_id'],
                'platforms': list(routing_result['platform_orders'].keys())
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to route order',
                'error': routing_result.get('error')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Webhook processing failed',
            'error': str(e)
        }), 500

@app.route('/webhooks/shopify/orders/update', methods=['POST'])
def handle_order_updated():
    """Handle Shopify order update webhook"""
    try:
        # Verify webhook authenticity
        hmac_header = request.headers.get('X-Shopify-Hmac-Sha256')
        if not verify_webhook(request.get_data(), hmac_header):
            return jsonify({'error': 'Invalid webhook signature'}), 401
        
        order_data = request.get_json()
        
        # Handle order updates (cancellations, modifications, etc.)
        # This would include logic to update or cancel orders on fulfillment platforms
        
        return jsonify({'status': 'success', 'message': 'Order update processed'}), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Webhook processing failed',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
def _add_fulfillment_metafields(self, shopify_product_id: int, fulfillment_platform: str, platform_data: Dict):
    """Add metafields for order routing"""
    metafields = [
        {
            'namespace': 'fulfillment',
            'key': 'platform',
            'value': fulfillment_platform,
            'type': 'single_line_text_field'
        },
        {
            'namespace': 'fulfillment',
            'key': 'platform_product_id',
            'value': str(platform_data.get('product_id', '')),
            'type': 'single_line_text_field'
        },
        {
            'namespace': 'fulfillment',
            'key': 'platform_data',
            'value': json.dumps(platform_data),
            'type': 'json'
        }
    ]
    
    for metafield_data in metafields:
        metafield = shopify.Metafield(metafield_data)
        metafield.owner_id = shopify_product_id
        metafield.owner_resource = 'product'
        metafield.save()

def _generate_tier_description(self, tier: str, platform: str, location: str) -> str:
    """Generate tier-appropriate product descriptions"""
    base_desc = f"Professional {location.lower()} photography captured from Instagram and optimized for premium printing."
    
    if tier == "Premium":
        return f"""
{base_desc}
Premium Fine Art Collection

Museum-quality archival printing
100+ year fade resistance guarantee
Certificate of authenticity included
Premium paper or canvas options
Professional mounting available
Perfect for collectors and galleries

Printed on demand using gallery-grade processes for exceptional quality and longevity.
""".strip()
    elif tier == "Professional":
        return f"""
{base_desc}
Professional Photography Collection

High-quality photographic printing
Fade-resistant inks and papers
Multiple size and material options
Professional presentation quality
Ready for framing or display
Ideal for home and office decoration

Premium printing with professional-grade materials and processes.
""".strip()
    else:  # Canvas
        return f"""
{base_desc}
Canvas Print Collection

High-quality canvas printing
Fade-resistant UV inks
Gallery-wrapped ready to hang
Multiple size options available
Perfect for modern home decor
Affordable fine art solution

Vibrant canvas prints that bring Instagram photography to life on your walls.
""".strip()
def _extract_location(self, hashtags: List[str]) -> str:
    """Extract location from hashtags"""
    location_keywords = ['landscape', 'mountains', 'ocean', 'forest', 'desert', 'city', 'beach', 'sunset', 'nature']
    for tag in hashtags:
        if any(keyword in tag.lower() for keyword in location_keywords):
            return tag.replace('#', '').title()
    return 'Scenic'