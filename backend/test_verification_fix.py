"""
Test the verification fix with a clean surface image
"""
import sys
import io
from PIL import Image
import numpy as np

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

print("Testing Verification Fix")
print("=" * 60)

# Create a clean smooth surface image (like the user's image)
print("\n1. Creating test clean surface image...")
test_img = Image.new('RGB', (500, 500), color=(180, 180, 180))  # Gray smooth surface

# Add some realistic shadows (dappled light effect)
pixels = test_img.load()
for i in range(0, 500, 50):
    for j in range(0, 500, 50):
        # Create shadow patches
        for x in range(i, min(i+30, 500)):
            for y in range(j, min(j+30, 500)):
                # Darken some areas
                r, g, b = pixels[x, y]
                pixels[x, y] = (int(r*0.7), int(g*0.7), int(b*0.7))

# Save to bytes
img_bytes = io.BytesIO()
test_img.save(img_bytes, format='JPEG')
test_img_bytes = img_bytes.getvalue()

print(f"✓ Created test image: {len(test_img_bytes)} bytes")

# Test the verifier
print("\n2. Loading verification module...")
from ml.verify_completion import WorkCompletionVerifier

verifier = WorkCompletionVerifier()
print("✓ Verifier loaded")

# Test surface quality check
print("\n3. Testing surface quality analysis...")
quality = verifier._check_surface_quality(test_img_bytes)
print(f"   Quality Score: {quality['quality_score']:.2f}")
print(f"   Edge Intensity: {quality['edge_intensity']:.2f}")
print(f"   Brightness Std: {quality['brightness_std']:.2f}")
print(f"   Is Likely Clean: {quality['is_likely_clean']}")

if quality['is_likely_clean']:
    print("✓ PASS: Clean surface correctly identified")
else:
    print("✗ FAIL: Clean surface not identified")

# Test classification
print("\n4. Testing image classification...")
classification = verifier.classify_image(test_img_bytes)
print(f"   Predicted Class: {classification['class']}")
print(f"   Confidence: {classification['confidence']:.1%}")
print(f"   All probabilities:")
for cls, prob in classification['all_probabilities'].items():
    print(f"      {cls}: {prob:.1%}")

print("\n" + "=" * 60)
print("Test Complete!")
print("\nInterpretation:")
if quality['is_likely_clean'] and quality['quality_score'] > 0.70:
    print("✓ The override logic WILL trigger for this image")
    print("✓ Even if classified as pothole, it will be VERIFIED")
else:
    print("⚠ The override logic may NOT trigger")
    print(f"  Need quality_score > 0.70 (current: {quality['quality_score']:.2f})")
