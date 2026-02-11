"""
Test script to demonstrate multi-issue detection capability.

This script tests the new secondary_issues feature that detects
multiple civic problems in a single image (e.g., garbage + pothole).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

from ml.classifier import ImageClassifier
import json

def test_multi_issue_detection():
    """Test the multi-issue detection feature."""
    
    print("=" * 70)
    print("MULTI-ISSUE DETECTION TEST")
    print("=" * 70)
    print("\nThis test demonstrates how the model now detects multiple civic")
    print("issues in a single image (e.g., garbage + pothole).\n")
    
    # Initialize classifier
    print("Loading model...")
    classifier = ImageClassifier()
    
    if classifier.model is None:
        print("❌ ERROR: Could not load model!")
        return
    
    print("✅ Model loaded successfully!\n")
    
    # Test with sample images from Dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "Dataset")
    
    test_cases = [
        ("Garbage", "Sample garbage image"),
        ("Potholes", "Sample pothole image"),
        ("water logging", "Sample waterlogging image"),
    ]
    
    for category, description in test_cases:
        category_path = os.path.join(dataset_path, category)
        
        if not os.path.exists(category_path):
            print(f"⚠️  Skipping {category} - directory not found")
            continue
        
        # Get first image in category
        images = [f for f in os.listdir(category_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not images:
            print(f"⚠️  Skipping {category} - no images found")
            continue
        
        test_image = os.path.join(category_path, images[0])
        
        print(f"\n{'='*70}")
        print(f"Testing: {description}")
        print(f"File: {os.path.basename(test_image)}")
        print(f"{'='*70}")
        
        # Read image
        with open(test_image, 'rb') as f:
            image_data = f.read()
        
        # Classify
        result = classifier.classify(image_data)
        
        # Display results
        print(f"\n📊 CLASSIFICATION RESULTS:")
        print(f"   Primary Issue: {result['predicted_class'].upper()}")
        print(f"   Confidence: {result['confidence']:.2%}")
        
        # Show all probabilities
        print(f"\n📈 ALL PROBABILITIES:")
        for cat, prob in sorted(result['all_probabilities'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(prob * 50)
            print(f"   {cat:20s} {prob:6.2%} {bar}")
        
        # Show secondary issues
        if result.get('secondary_issues'):
            print(f"\n🔍 SECONDARY ISSUES DETECTED:")
            for issue in result['secondary_issues']:
                print(f"   • {issue['category'].upper()}: {issue['confidence_percent']}% confidence")
            print(f"\n   ✅ Multiple issues found in this image!")
        else:
            print(f"\n   ℹ️  No secondary issues above 30% threshold")
        
        print(f"\n💡 INTERPRETATION:")
        if result.get('secondary_issues'):
            print(f"   This image contains multiple civic problems:")
            print(f"   - Primary: {result['predicted_class']} ({result['confidence']:.1%})")
            for issue in result['secondary_issues']:
                print(f"   - Also: {issue['category']} ({issue['confidence_percent']}%)")
        else:
            print(f"   This image clearly shows a single issue: {result['predicted_class']}")
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n💡 HOW IT WORKS:")
    print("   - Model calculates probabilities for all 4 categories")
    print("   - Primary issue = highest probability (as before)")
    print("   - Secondary issues = any civic issue with >30% confidence")
    print("   - Example: Garbage (45%) + Pothole (42%) = Both detected!")
    print("\n✅ Your model can now report multiple issues in one image!")

if __name__ == "__main__":
    test_multi_issue_detection()
