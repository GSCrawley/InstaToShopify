# src/phase3_multi_tier_fulfillment/monitoring/health_checker.py
import requests
import time
from typing import Dict, List
from datetime import datetime
import logging

class PlatformHealthMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.health_status = {
            'creativehub': {'status': 'unknown', 'last_check': None, 'consecutive_failures': 0},
            'shopify': {'status': 'unknown', 'last_check': None, 'consecutive_failures': 0},
            'printify': {'status': 'unknown', 'last_check': None, 'consecutive_failures': 0}
        }
    
    def check_all_platforms(self) -> Dict:
        """Check health of all platforms"""
        results = {}
        
        # Check CreativeHub
        results['creativehub'] = self._check_creativehub()
        
        # Check Shopify
        results['shopify'] = self._check_shopify()
        
        # Check Printify
        results['printify'] = self._check_printify()
        
        # Update internal status
        for platform, result in results.items():
            self.health_status[platform].update({
                'status': 'healthy' if result['responsive'] else 'down',
                'last_check': datetime.now(),
                'consecutive_failures': 0 if result['responsive'] else 
                    self.health_status[platform]['consecutive_failures'] + 1
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': self._calculate_overall_health(results),
            'platforms': results,
            'routing_recommendations': self._get_routing_recommendations()
        }
    
    def _check_creativehub(self) -> Dict:
        """Check CreativeHub API health"""
        try:
            from ..creativehub_integration.api_client import CreativeHubClient
            client = CreativeHubClient(use_sandbox=True)
            
            start_time = time.time()
            response = client.query_products(page=1, page_size=1)
            response_time = time.time() - start_time
            
            return {
                'platform': 'creativehub',
                'responsive': 'Data' in response,
                'response_time_ms': round(response_time * 1000, 2),
                'error': None
            }
        except Exception as e:
            return {
                'platform': 'creativehub', 
                'responsive': False,
                'response_time_ms': None,
                'error': str(e)
            }
    
    def _check_shopify(self) -> Dict:
        """Check Shopify API health"""
        try:
            # This would use your Shopify client
            start_time = time.time()
            # Make a simple API call to Shopify
            response_time = time.time() - start_time
            
            return {
                'platform': 'shopify',
                'responsive': True,  # Placeholder
                'response_time_ms': round(response_time * 1000, 2),
                'error': None
            }
        except Exception as e:
            return {
                'platform': 'shopify',
                'responsive': False, 
                'response_time_ms': None,
                'error': str(e)
            }
    
    def _check_printify(self) -> Dict:
        """Check Printify API health"""
        try:
            from ..printify_integration.printify_client import PrintifyManager
            manager = PrintifyManager()
            
            start_time = time.time()
            response = requests.get(
                f'{manager.base_url}/shops.json',
                headers=manager.headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            return {
                'platform': 'printify',
                'responsive': response.status_code == 200,
                'response_time_ms': round(response_time * 1000, 2),
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'platform': 'printify',
                'responsive': False,
                'response_time_ms': None, 
                'error': str(e)
            }
    
    def _calculate_overall_health(self, results: Dict) -> str:
        """Calculate overall system health"""
        healthy_count = sum(1 for r in results.values() if r['responsive'])
        total_count = len(results)
        
        if healthy_count == total_count:
            return 'excellent'
        elif healthy_count >= total_count * 0.67:
            return 'good'
        elif healthy_count >= total_count * 0.33:
            return 'degraded'
        else:
            return 'critical'
    
    def _get_routing_recommendations(self) -> List[str]:
        """Get platform routing recommendations based on health"""
        recommendations = []
        
        for platform, status in self.health_status.items():
            if status['consecutive_failures'] >= 3:
                recommendations.append(f"Avoid {platform} - multiple consecutive failures")
            elif status['consecutive_failures'] >= 1:
                recommendations.append(f"Use {platform} with caution - recent failure")
        
        if not recommendations:
            recommendations.append("All platforms healthy - use normal routing")
        
        return recommendationsqwdq