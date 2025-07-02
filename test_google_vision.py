#!/usr/bin/env python3
"""
Google Vision API Diagnostic Script
Tests if Google Vision API is properly configured and working.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_vision_setup():
    """Test Google Vision API setup and connectivity."""
    
    print("🔍 Testing Google Vision API Setup")
    print("=" * 50)
    
    # Test 1: Check if google-cloud-vision is installed
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        print("✅ Google Cloud Vision library is installed")
    except ImportError as e:
        print(f"❌ Google Cloud Vision library not installed: {e}")
        print("   Install with: pip install google-cloud-vision")
        return False
    
    # Test 2: Check environment variables
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("   Set it to point to your service account JSON file")
        return False
    else:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS set to: {credentials_path}")
    
    # Test 3: Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found at: {credentials_path}")
        return False
    else:
        print(f"✅ Credentials file exists")
    
    # Test 4: Try to load credentials
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        print("✅ Credentials loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        return False
    
    # Test 5: Try to create Vision client
    try:
        client = vision.ImageAnnotatorClient(credentials=credentials)
        print("✅ Vision API client created successfully")
    except Exception as e:
        print(f"❌ Failed to create Vision API client: {e}")
        return False
    
    # Test 6: Try a simple API call with a test image
    try:
        # Create a simple test image (1x1 pixel)
        from PIL import Image
        import io
        
        # Create a tiny test image
        test_image = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # Test Vision API call
        image = vision.Image(content=img_byte_arr.getvalue())
        response = client.label_detection(image=image)
        
        if response.error.message:
            print(f"❌ Vision API error: {response.error.message}")
            return False
        else:
            print("✅ Vision API call successful")
            if response.label_annotations:
                print(f"   Found {len(response.label_annotations)} labels")
                for label in response.label_annotations[:3]:
                    print(f"   - {label.description} (confidence: {label.score:.2f})")
            else:
                print("   No labels detected (normal for test image)")
        
    except Exception as e:
        print(f"❌ Vision API call failed: {e}")
        return False
    
    print("\n🎉 Google Vision API is working correctly!")
    return True

def test_with_sample_image():
    """Test with a real image if available."""
    
    # Look for sample images in the project
    sample_dirs = ['data/raw/original', 'data/raw', 'data/original', 'photography_automation_data/raw_photos/original']
    sample_image = None
    
    for dir_path in sample_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    sample_image = os.path.join(dir_path, file)
                    break
            if sample_image:
                break
    
    if not sample_image:
        print("\n📷 No sample images found for testing")
        return
    
    print(f"\n📷 Testing with sample image: {sample_image}")
    print("-" * 50)
    
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = vision.ImageAnnotatorClient(credentials=credentials)
        
        # Read the image
        with open(sample_image, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Request label detection
        response = client.label_detection(image=image, max_results=10)
        
        if response.error.message:
            print(f"❌ Error analyzing image: {response.error.message}")
            return
        
        print("✅ Image analysis successful!")
        print("\nDetected labels:")
        for label in response.label_annotations:
            print(f"  - {label.description} (confidence: {label.score:.2f})")
        
        # Test object detection too
        response = client.object_localization(image=image)
        if response.localized_object_annotations:
            print("\nDetected objects:")
            for obj in response.localized_object_annotations:
                print(f"  - {obj.name} (confidence: {obj.score:.2f})")
        
    except Exception as e:
        print(f"❌ Error testing with sample image: {e}")

if __name__ == "__main__":
    print("Google Vision API Diagnostic Tool")
    print("=" * 40)
    
    # Test basic setup
    if test_google_vision_setup():
        # Test with real image if available
        test_with_sample_image()
    else:
        print("\n🔧 Please fix the issues above and try again")
        
    print("\n" + "=" * 40)
    print("Diagnostic complete!")
