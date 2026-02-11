"""
Test Work Completion Verification API
======================================
Simple test to verify the integration works
"""

import requests
import os

# Configuration
API_BASE_URL = "http://localhost:8000/api"
COMPLAINT_ID = 1  # Change this to an actual complaint ID in your database

# Test images (you need to provide actual images)
BEFORE_IMAGE_PATH = "test_pothole_before.jpg"  # Original complaint image
AFTER_IMAGE_PATH = "test_pothole_after.jpg"    # After completion image

def test_verify_completion():
    """Test the work completion verification endpoint."""
    
    print("=" * 80)
    print("TESTING WORK COMPLETION VERIFICATION API")
    print("=" * 80)
    
    # Step 1: Login (you need valid credentials)
    print("\n[1/3] Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": "admin@civiclens.com",  # Change to your admin email
            "password": "password123"         # Change to your admin password
        }
    )
    
    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✓ Logged in successfully")
    
    # Step 2: Verify completion
    print(f"\n[2/3] Verifying completion for complaint {COMPLAINT_ID}...")
    
    if not os.path.exists(AFTER_IMAGE_PATH):
        print(f"✗ After image not found: {AFTER_IMAGE_PATH}")
        print("\nTo test properly, provide:")
        print("1. BEFORE_IMAGE_PATH - Original complaint image")
        print("2. AFTER_IMAGE_PATH - Completion verification image")
        return
    
    with open(AFTER_IMAGE_PATH, 'rb') as f:
        files = {'after_image': f}
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            f"{API_BASE_URL}/complaints/{COMPLAINT_ID}/verify-completion",
            files=files,
            headers=headers
        )
    
    # Step 3: Check result
    print(f"\n[3/3] Response:")
    print("-" * 80)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Request successful!")
        print(f"\nVerification Result:")
        print(f"  Complaint ID: {result['complaint_id']}")
        print(f"  Tracking ID: {result['tracking_id']}")
        print(f"  Verified: {result['verified']}")
        print(f"  Decision: {result['decision']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Message: {result['message']}")
        print(f"  Status Updated: {result['status_updated']}")
        
        if result.get('after_image_url'):
            print(f"  After Image: {result['after_image_url']}")
        
        # Show details
        if 'details' in result:
            details = result['details']
            print(f"\nDetails:")
            if 'location_similarity' in details:
                print(f"  Location Similarity: {details['location_similarity']:.2%}")
            
            if 'before_classification' in details:
                before = details['before_classification']
                print(f"  Before: {before['original_class']} ({before['confidence']:.1%})")
            
            if 'after_classification' in details:
                after = details['after_classification']
                print(f"  After: {after['original_class']} ({after['confidence']:.1%})")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"Error: {response.text}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\nNOTE: Make sure:")
    print("1. Backend server is running (uvicorn app.main:app)")
    print("2. Database migration is applied (migration_verification.sql)")
    print("3. You have valid test images")
    print("4. COMPLAINT_ID exists in your database")
    print()
    
    # Uncomment to run test
    # test_verify_completion()
    
    print("Update the configuration in this file and uncomment the test call to run.")
