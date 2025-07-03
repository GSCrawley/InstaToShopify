# src/phase3_multi_tier_fulfillment/creativehub_integration/error_handler.py
import time
import logging
from typing import Dict, Callable
from functools import wraps

class CreativeHubErrorHandler:
    def __init__(self, max_retries: int = 3, fallback_delay: int = 300):
        self.max_retries = max_retries
        self.fallback_delay = fallback_delay
        self.logger = logging.getLogger(__name__)
        
    def with_retry_and_fallback(self, fallback_function: Callable = None):
        """Decorator for retry logic with fallback options"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(self.max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        if result.get('success'):
                            return result
                        else:
                            raise Exception(f"Function failed: {result.get('error')}")
                            
                    except Exception as e:
                        last_exception = e
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}"
                        )
                        
                        if attempt < self.max_retries:
                            time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                # All retries failed, try fallback
                if fallback_function:
                    self.logger.info(f"Attempting fallback for {func.__name__}")
                    try:
                        time.sleep(self.fallback_delay)
                        return fallback_function(*args, **kwargs)
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback also failed: {str(fallback_error)}")
                
                # Return failure result
                return {
                    'success': False,
                    'error': f"All attempts failed. Last error: {str(last_exception)}",
                    'platform': 'creativehub',
                    'fallback_attempted': fallback_function is not None
                }
            return wrapper
        return decorator
    
    def check_platform_health(self) -> bool:
        """Check if CreativeHub is responsive"""
        from .api_client import CreativeHubClient
        
        try:
            client = CreativeHubClient(use_sandbox=True)
            response = client.query_products(page=1, page_size=1)
            return 'Data' in response
        except Exception as e:
            self.logger.error(f"CreativeHub health check failed: {str(e)}")
            return False