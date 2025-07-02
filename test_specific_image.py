#!/usr/bin/env python3
"""
Test Google Vision API with specific images to understand content detection
"""

import os
import sys
from google.cloud import vision
from google.oauth2 import service_account

def analyze_image(image_path):
    """Analyze a specific image with Google Vision API."""
    
    print(f"🔍 Analyzing: {image_path}")
    print("=" * 60)
    
    try:
        # Setup Vision API client
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = vision.ImageAnnotatorClient(credentials=credentials)
        
        # Read the image
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Request label detection
        response = client.label_detection(image=image, max_results=15)
        
        if response.error.message:
            print(f"❌ Error analyzing image: {response.error.message}")
            return
        
        print("✅ Image analysis successful!")
        print("\nDetected labels:")
        for i, label in enumerate(response.label_annotations, 1):
            print(f"  {i:2d}. {label.description} (confidence: {label.score:.2f})")
        
        # Test object detection too
        response = client.object_localization(image=image)
        if response.localized_object_annotations:
            print("\nDetected objects:")
            for i, obj in enumerate(response.localized_object_annotations, 1):
                print(f"  {i:2d}. {obj.name} (confidence: {obj.score:.2f})")
        else:
            print("\nNo specific objects detected")
            
        # Test text detection (in case it's a video thumbnail with text)
        response = client.text_detection(image=image)
        if response.text_annotations:
            print("\nDetected text:")
            for i, text in enumerate(response.text_annotations[:5], 1):
                print(f"  {i:2d}. '{text.description.strip()}' (confidence: {text.confidence if hasattr(text, 'confidence') else 'N/A'})")
        else:
            print("\nNo text detected")
        
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")

def main():
    # Test multiple images
    image_dir = "data/raw/original"
    
    if not os.path.exists(image_dir):
        print(f"❌ Directory not found: {image_dir}")
        return
    
    images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not images:
        print(f"❌ No images found in {image_dir}")
        return
    
    print(f"Found {len(images)} images to analyze")
    print("=" * 60)
    
    # Analyze first few images
    for i, image_file in enumerate(images[:3]):  # Test first 3 images
        image_path = os.path.join(image_dir, image_file)
        analyze_image(image_path)
        
        if i < len(images[:3]) - 1:  # Don't print separator after last image
            print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
