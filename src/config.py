import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Apify
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')

# Google Cloud Storage
GOOGLE_APPLICATION_CREDENTIALS WQgetenv('ETSY_API_KEY')

# Shopify
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_SECRET_KEY = os.getenv('SHOPIFY_API_SECRET_KEY')
SHOPIFY_STORE_NAME = os.getenv('SHOPIFY_STORE_NAME')
STOREFRONT_ACCESS_TOKEN = os.getenv('STOREFRONT_ACCESS_TOKEN')
SHOPIFY_ADMIN_API_TOKEN = os.getenv('SHOPIFY_ADMIN_API_TOKEN')

WHITEWALL_API_TOKEN = os.getenv('WHITEWALL_API_TOKEN')
CREATIVE_HUB_API_KEY = os.getenv('CREATIVE_HUB_API_KEY')
CREATIVEHUB_BASE_URL = os.getenv('CREATIVEHUB_BASE_URL', 'https://api.creativehub.io')
CREATIVEHUB_SANDBOX_API_KEY = os.getenv('CREATIVEHUB_SANDBOX_API_KEY')
CREATIVEHUB_SANDBOX_BASE_URL = os.getenv('CREATIVEHUB_SANDBOX_BASE_URL', 'https://api.sandbox.creativehub.io')

# Printify
PRINTIFY_API_TOKEN = os.getenv('PRINTIFY_API_TOKEN')
PRINTIFY_SHOP_ID = os.getenv('PRINTIFY_SHOP_ID')

# Instagram Scraper Configuration
# Expects comma-separated full Instagram profile URLs (e.g., https://www.instagram.com/username/)
INSTAGRAM_TARGET_PROFILES = [url.strip() for url in os.getenv('INSTAGRAM_TARGET_PROFILES', '').split(',') if url.strip()]

# Computer Vision Filtering
# Comma-separated descriptive terms for the CV model to filter images by (e.g., 'sunset', 'nyc street at dusk')
CV_CONTENT_DESCRIPTIONS_FILTER = [desc.strip() for desc in os.getenv('CV_CONTENT_DESCRIPTIONS_FILTER', '').split(',') if desc.strip()]

# Enhanced Content Filtering Configuration
# Content categories to match against (landscape, sunset, water, nature, mountains, urban)
ENHANCED_CONTENT_CATEGORIES = [cat.strip() for cat in os.getenv('ENHANCED_CONTENT_CATEGORIES', 'landscape,sunset,water,nature,mountains,urban').split(',') if cat.strip()]

# Quality and scoring thresholds for enhanced filtering
MIN_QUALITY_SCORE = float(os.getenv('MIN_QUALITY_SCORE', '0.5'))
MIN_CATEGORY_SCORE = float(os.getenv('MIN_CATEGORY_SCORE', '0.5'))
MIN_OVERALL_SCORE = float(os.getenv('MIN_OVERALL_SCORE', '0.6'))
MIN_PRINT_SUITABILITY = float(os.getenv('MIN_PRINT_SUITABILITY', '0.4'))

# Enhanced filtering options
USE_ENHANCED_FILTERING = os.getenv('USE_ENHANCED_FILTERING', 'true').lower() == 'true'
USE_GCS = os.getenv('USE_GCS', 'false').lower() == 'true'

# Basic check to ensure critical tokens are loaded
if not APIFY_API_TOKEN:
    print("Warning: APIFY_API_TOKEN not found in .env file.")

if not GOOGLE_APPLICATION_CREDENTIALS or not GCS_BUCKET_NAME:
    print("Warning: Google Cloud Storage configuration (credentials or bucket name) not found in .env file.")

# Add more checks as needed for Etsy, Printify etc.
