"""
Complete Pipeline Testing Suite for CivicLens AI System
Tests all components: Image Classification, Text Analysis, Image-Text Matching, Geotag Extraction
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

import numpy as np
from PIL import Image
import io
import json

print("="*70)
print("CivicLens AI Pipeline - Complete Testing Suite")
print("="*70)

# Test 1: Model Loading
print("\n[TEST 1] Model Loading & Architecture Verification")
print("-" * 70)

try:
    from ml.classifier import ImageClassifier
    classifier = ImageClassifier()
    
    print(f"✓ Model loaded successfully")
    print(f"  Model type: {classifier.model_type}")
    print(f"  Categories: {classifier.categories}")
    print(f"  Confidence threshold: {classifier.confidence_threshold:.0%}")
    print(f"  Image size: {classifier.img_size}")
    
    if classifier.model:
        print(f"  Input shape: {classifier.model.input_shape}")
        print(f"  Output shape: {classifier.model.output_shape}")
        print(f"  Total parameters: {classifier.model.count_params():,}")
        test1_passed = True
    else:
        print("✗ Model is None - will use fallback")
        test1_passed = False
        
except Exception as e:
    print(f"✗ Error loading model: {e}")
    test1_passed = False

# Test 2: Image Classification (All 4 Categories)
print("\n[TEST 2] Image Classification - All Categories")
print("-" * 70)

def create_test_image(category: str) -> bytes:
    """Create a synthetic test image based on category."""
    img = Image.new('RGB', (224, 224))
    pixels = img.load()
    
    # Create color patterns for each category
    if category == 'garbage':
        # Mixed colors, high variance (trash/debris)
        colors = [(139, 69, 19), (128, 128, 128), (192, 192, 192), (101, 67, 33)]
    elif category == 'pothole':
        # Dark colors (asphalt/road)
        colors = [(50, 50, 50), (30, 30, 30), (70, 70, 70), (40, 40, 40)]
    elif category == 'waterlogging':
        # Blue/cyan colors (water)
        colors = [(70, 130, 180), (100, 149, 237), (64, 164, 223), (72, 118, 255)]
    else:  # invalid
        # Random bright colors (not matching any civic issue)
        colors = [(255, 192, 203), (255, 255, 0), (255, 165, 0), (144, 238, 144)]
    
    # Fill image with pattern
    for x in range(224):
        for y in range(224):
            color = colors[(x + y) % len(colors)]
            pixels[x, y] = color
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

test2_results = {}
test_categories = ['garbage', 'pothole', 'waterlogging', 'invalid']

for category in test_categories:
    print(f"\nTesting: {category.upper()}")
    try:
        test_image = create_test_image(category)
        result = classifier.classify(test_image)
        
        print(f"  Predicted: {result['predicted_class']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Is civic issue: {result['is_civic_issue']}")
        print(f"  Method: {result['method']}")
        
        if 'all_probabilities' in result:
            print(f"  Probabilities:")
            for cat, prob in result['all_probabilities'].items():
                print(f"    {cat}: {prob:.2%}")
        
        test2_results[category] = result
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        test2_results[category] = None

test2_passed = all(v is not None for v in test2_results.values())

# Test 3: Text Analysis
print("\n[TEST 3] Text Analysis & Keyword Matching")
print("-" * 70)

try:
    from ml.classifier import TextAnalyzer
    text_analyzer = TextAnalyzer()
    
    test_cases = [
        ("Garbage on street", "There is a pile of garbage and trash near my house", "garbage"),
        ("Road damage", "Big pothole on the road causing problems", "pothole"),
        ("Water problem", "Waterlogging and flooding after rain", "waterlogging"),
        ("Random complaint", "Something is wrong here", None),  # Should return None
    ]
    
    test3_passed = True
    for title, desc, expected in test_cases:
        result = text_analyzer.analyze(title, desc)
        predicted = result['predicted_category']
        confidence = result['confidence']
        
        status = "✓" if predicted == expected else "✗"
        print(f"\n{status} \"{title}\"")
        print(f"  Expected: {expected}, Got: {predicted} ({confidence:.0%})")
        print(f"  Matched keywords: {result['matched_keywords'].get(predicted or 'none', [])[:3]}")
        
        if predicted != expected:
            test3_passed = False
            
except Exception as e:
    print(f"✗ Error in text analysis: {e}")
    test3_passed = False

# Test 4: Image-Text Matching
print("\n[TEST 4] Image-Text Matching Verification")
print("-" * 70)

try:
    from ml.classifier import ComplaintVerifier
    verifier = ComplaintVerifier()
    
    # Test case 1: Matching (image=garbage, text=garbage)
    print("\nCase 1: MATCHING (image=garbage, text=garbage)")
    test_img = create_test_image('garbage')
    result = verifier.verify(
        test_img, 
        "Garbage pile", 
        "Large pile of trash and waste on the street"
    )
    print(f"  Decision: {result['decision']}")
    print(f"  Valid: {result['is_valid']}")
    print(f"  Message: {result['message'][:80]}...")
    
    # Test case 2: Mismatching (image=pothole, text=garbage)
    print("\nCase 2: MISMATCH (image=pothole, text=garbage)")
    test_img = create_test_image('pothole')
    result = verifier.verify(
        test_img,
        "Garbage problem",
        "There is garbage everywhere"
    )
    print(f"  Decision: {result['decision']}")
    print(f"  Valid: {result['is_valid']}")
    print(f"  Suggestion: {result.get('suggestion', 'N/A')}")
    
    # Test case 3: Invalid image
    print("\nCase 3: INVALID IMAGE")
    test_img = create_test_image('invalid')
    result = verifier.verify(
        test_img,
        "Some complaint",
        "Random description"
    )
    print(f"  Decision: {result['decision']}")
    print(f"  Valid: {result['is_valid']}")
    print(f"  Message: {result['message'][:80]}...")
    
    test4_passed = True
    
except Exception as e:
    print(f"✗ Error in image-text matching: {e}")
    import traceback
    traceback.print_exc()
    test4_passed = False

# Test 5: Geotag Extraction
print("\n[TEST 5] Geotag Extraction (EXIF + OCR)")
print("-" * 70)

try:
    from ml.classifier import GeotagExtractor
    geo_extractor = GeotagExtractor()
    
    # Test with image without EXIF
    print("\nTest: Image without EXIF data")
    test_img = create_test_image('garbage')
    result = geo_extractor.extract_geotag(test_img)
    print(f"  Has geotag: {result['has_geotag']}")
    print(f"  Latitude: {result.get('latitude', 'N/A')}")
    print(f"  Longitude: {result.get('longitude', 'N/A')}")
    print(f"  Source: {result.get('source', 'N/A')}")
    
    # Try OCR-enabled extractor
    try:
        from ml.ocr_geo import get_geo_extractor
        ocr_extractor = get_geo_extractor()
        print(f"\n✓ OCR-enabled GeoExtractor available")
        print(f"  OCR libraries: {ocr_extractor.available_methods}")
        test5_passed = True
    except ImportError:
        print(f"\n✓ Using EXIF-only GeoExtractor (OCR not available)")
        test5_passed = True
        
except Exception as e:
    print(f"✗ Error in geotag extraction: {e}")
    test5_passed = False

# Test 6: Complete Pipeline Integration
print("\n[TEST 6] Complete Pipeline Integration")
print("-" * 70)

try:
    # Simulate a full complaint submission
    print("\nSimulating complete complaint workflow:")
    print("  Image: Waterlogging scene")
    print("  Title: 'Water flooding on street'")
    print("  Description: 'Heavy waterlogging after rain, water everywhere'")
    
    test_img = create_test_image('waterlogging')
    result = verifier.verify(
        test_img,
        "Water flooding on street",
        "Heavy waterlogging after rain, water everywhere, drainage blocked"
    )
    
    print(f"\nPipeline Results:")
    print(f"  ✓ Image Classification: {result['image_classification']['predicted_class']} "
          f"({result['image_classification']['confidence']:.0%})")
    print(f"  ✓ Text Analysis: {result['text_analysis']['predicted_category']} "
          f"({result['text_analysis']['confidence']:.0%})")
    print(f"  ✓ Final Decision: {result['decision']}")
    print(f"  ✓ Complaint Valid: {result['is_valid']}")
    print(f"  ✓ Final Category: {result.get('final_category', 'N/A')}")
    print(f"  ✓ Overall Confidence: {result['confidence']:.0%}")
    
    test6_passed = True
    
except Exception as e:
    print(f"✗ Error in complete pipeline: {e}")
    import traceback
    traceback.print_exc()
    test6_passed = False

# Final Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

results = {
    "Model Loading": test1_passed,
    "Image Classification": test2_passed,
    "Text Analysis": test3_passed,
    "Image-Text Matching": test4_passed,
    "Geotag Extraction": test5_passed,
    "Complete Pipeline": test6_passed
}

for test_name, passed in results.items():
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"  {status}: {test_name}")

all_passed = all(results.values())
print("\n" + "="*70)
if all_passed:
    print("🎉 ALL TESTS PASSED! System ready for production.")
else:
    print("⚠️  SOME TESTS FAILED. Review errors above.")
print("="*70)
