"""
Test the FastAPI endpoint with the AI pipeline
"""

import requests
import io
from PIL import Image
import json

def create_test_image(category: str) -> bytes:
    """Create a test image."""
    img = Image.new('RGB', (224, 224))
    pixels = img.load()
    
    if category == 'garbage':
        colors = [(139, 69, 19), (128, 128, 128), (192, 192, 192), (101, 67, 33)]
    elif category == 'pothole':
        colors = [(50, 50, 50), (30, 30, 30), (70, 70, 70), (40, 40, 40)]
    elif category == 'waterlogging':
        colors = [(70, 130, 180), (100, 149, 237), (64, 164, 223), (72, 118, 255)]
    else:
        colors = [(255, 192, 203), (255, 255, 0), (255, 165, 0), (144, 238, 144)]
    
    for x in range(224):
        for y in range(224):
            color = colors[(x + y) % len(colors)]
            pixels[x, y] = color
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

print("="*70)
print("Testing CivicLens API Endpoint")
print("="*70)

BASE_URL = "http://localhost:8000"

# Check if server is running
try:
    response = requests.get(f"{BASE_URL}/", timeout=2)
    print(f"\n✓ Server is running at {BASE_URL}")
except requests.exceptions.ConnectionError:
    print(f"\n✗ Server is NOT running at {BASE_URL}")
    print("  Please start the server with: uvicorn app.main:app --reload")
    exit(1)

# Test AI verification endpoint
print("\n[TEST] AI-Powered Complaint Verification")
print("-" * 70)

test_cases = [
    {
        "title": "Garbage pile on street",
        "description": "Large pile of trash and waste near the market area",
        "category": "garbage",
        "image": "garbage"
    },
    {
        "title": "Big pothole on road",
        "description": "Dangerous pothole causing damage to vehicles",
        "category": "pothole",
        "image": "pothole"
    },
    {
        "title": "Water flooding",
        "description": "Heavy waterlogging after rain, drainage blocked",
        "category": "waterlogging",
        "image": "waterlogging"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['title']}")
    print("-" * 70)
    
    try:
        # Create test image
        image_data = create_test_image(test['image'])
        
        # Prepare request
        files = {
            'image': ('test.png', image_data, 'image/png')
        }
        data = {
            'title': test['title'],
            'description': test['description'],
            'category': test['category']
        }
        
        # Send request
        response = requests.post(
            f"{BASE_URL}/api/complaints/verify",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Status: ✓ SUCCESS (200)")
            print(f"  Decision: {result.get('decision', 'N/A')}")
            print(f"  Valid: {result.get('is_valid', False)}")
            print(f"  Confidence: {result.get('confidence', 0):.0%}")
            print(f"  Message: {result.get('message', '')[:100]}")
            if result.get('image_classification'):
                print(f"  Image: {result['image_classification']['predicted_class']} "
                      f"({result['image_classification']['confidence']:.0%})")
            if result.get('text_analysis'):
                print(f"  Text: {result['text_analysis']['predicted_category']} "
                      f"({result['text_analysis']['confidence']:.0%})")
        else:
            print(f"  Status: ✗ ERROR ({response.status_code})")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "="*70)
print("API Testing Complete")
print("="*70)
