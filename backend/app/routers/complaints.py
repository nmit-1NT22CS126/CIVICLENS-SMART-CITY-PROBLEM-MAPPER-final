from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from .. import schemas, auth
from ..supabase_client import supabase, STORAGE_BUCKET
import uuid
import random
from datetime import datetime
import logging
import sys
import os

# Add ml directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml'))

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Complaints"]
)

# Initialize classifier (lazy loading to avoid slow startup)
_classifier = None
_verifier = None
_work_verifier = None

def get_classifier():
    """Get or initialize the image classifier."""
    global _classifier
    if _classifier is None:
        try:
            from ml.classifier import ImageClassifier
            _classifier = ImageClassifier()
            logger.info("Image classifier initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize classifier: {e}")
            _classifier = "failed"
    return _classifier if _classifier != "failed" else None


def get_verifier():
    """Get or initialize the complaint verifier."""
    global _verifier
    if _verifier is None:
        try:
            from ml.classifier import get_verifier as create_verifier
            _verifier = create_verifier()
            logger.info("Complaint verifier initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize verifier: {e}")
            _verifier = "failed"
    return _verifier if _verifier != "failed" else None


def get_work_verifier():
    """Get or initialize the work completion verifier."""
    global _work_verifier
    if _work_verifier is None:
        try:
            from ml.verify_completion import WorkCompletionVerifier
            _work_verifier = WorkCompletionVerifier()
            logger.info("Work completion verifier initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize work verifier: {e}")
            _work_verifier = "failed"
    return _work_verifier if _work_verifier != "failed" else None


def get_geotag_extractor():
    """
    Get enhanced geotag extractor with OCR support.
    Falls back to EXIF-only extraction if OCR libraries not available.
    """
    try:
        # Try the new OCR-enabled extractor first
        from ml.ocr_geo import get_geo_extractor
        logger.info("Using OCR-enabled GeoExtractor")
        return get_geo_extractor()
    except ImportError:
        # Fallback to original EXIF-only extractor
        try:
            from ml.classifier import GeotagExtractor
            logger.info("Using EXIF-only GeotagExtractor")
            return GeotagExtractor()
        except Exception as e:
            logger.warning(f"Could not import GeotagExtractor: {e}")
            return None
    except Exception as e:
        logger.warning(f"Could not import GeoExtractor: {e}")
        return None


def generate_tracking_id() -> str:
    """Generate a unique tracking ID"""
    return f"CVC-{random.randint(1000, 9999)}-{datetime.now().year}"


# ============================================================================
# CATEGORY NORMALIZATION - Central mapping for all category comparisons
# ============================================================================
# Model outputs: Garbage, Invalid_data, Potholes, water logging
# We normalize everything to: garbage, pothole, waterlogging, invalid

def normalize_category(category: str) -> str:
    """
    Normalize any category string to our standard internal format.
    Returns: 'garbage', 'pothole', 'waterlogging', 'invalid', or None
    """
    if not category:
        return None
    
    cat_lower = category.lower().strip()
    
    # Comprehensive mapping covering all variations
    mappings = {
        # Garbage variations
        'garbage': 'garbage',
        'trash': 'garbage',
        'waste': 'garbage',
        'rubbish': 'garbage',
        'dump': 'garbage',
        'litter': 'garbage',
        'dirty': 'garbage',
        'debris': 'garbage',
        
        # Pothole variations
        'pothole': 'pothole',
        'potholes': 'pothole',
        'road damage': 'pothole',
        'road hole': 'pothole',
        'broken road': 'pothole',
        'crack': 'pothole',
        
        # Waterlogging variations (CRITICAL: handle space and underscore)
        'waterlogging': 'waterlogging',
        'water logging': 'waterlogging',  # Model output has space!
        'water_logging': 'waterlogging',
        'flooding': 'waterlogging',
        'flood': 'waterlogging',
        'water': 'waterlogging',
        
        # Invalid variations
        'invalid': 'invalid',
        'invalid_data': 'invalid',  # Model output
        'invalid data': 'invalid',
        'no issue': 'invalid',
        'no_issue': 'invalid',
        'irrelevant': 'invalid',
        'other': 'invalid',
        'unknown': 'invalid',
    }
    
    return mappings.get(cat_lower, None)


def display_category(normalized_cat: str) -> str:
    """Convert normalized category to user-friendly display name."""
    display_map = {
        'garbage': 'Garbage',
        'pothole': 'Pothole',
        'waterlogging': 'Waterlogging',
        'invalid': 'Invalid/Irrelevant'
    }
    return display_map.get(normalized_cat, 'Unknown')


def analyze_text_for_category(title: str, description: str) -> dict:
    """
    Analyze complaint text to determine what category the user is describing.
    This is CRITICAL for text vs image matching.
    
    Returns: {
        'category': normalized category or None,
        'confidence': float 0-1,
        'matched_keywords': list of matched keywords
    }
    """
    text = f"{title} {description}".lower()
    
    # Keywords for each category (ordered by specificity - most specific first)
    category_keywords = {
        'garbage': [
            'garbage', 'trash', 'waste', 'rubbish', 'dump', 'litter', 'dirty',
            'debris', 'refuse', 'junk', 'bin', 'dustbin', 'garbage dump',
            'waste pile', 'littering', 'plastic waste', 'scrap', 'unhygienic',
            'filth', 'sanitation', 'pile of garbage', 'dump yard'
        ],
        'pothole': [
            'pothole', 'pot hole', 'road damage', 'road hole', 'broken road',
            'crater', 'pit', 'road crack', 'damaged road', 'road repair',
            'uneven road', 'bumpy road', 'road surface', 'pavement damage',
            'asphalt', 'hole in road', 'road condition'
        ],
        'waterlogging': [
            'waterlogging', 'water logging', 'flood', 'flooding', 'water on road',
            'standing water', 'water accumulation', 'drainage', 'drain blocked',
            'blocked drain', 'puddle', 'stagnant water', 'rain water',
            'water stagnation', 'submerged', 'clogged drain', 'sewage overflow'
        ]
    }
    
    # Count matches for each category
    scores = {}
    matched = {}
    
    for cat, keywords in category_keywords.items():
        matches = [kw for kw in keywords if kw in text]
        scores[cat] = len(matches)
        matched[cat] = matches
    
    # Find the category with highest score
    max_score = max(scores.values()) if scores else 0
    
    if max_score == 0:
        return {'category': None, 'confidence': 0.0, 'matched_keywords': []}
    
    # Get winning category
    winning_cat = max(scores, key=scores.get)
    
    # Calculate confidence (3+ matches = high confidence)
    confidence = min(1.0, max_score / 3.0)
    
    return {
        'category': winning_cat,
        'confidence': confidence,
        'matched_keywords': matched[winning_cat]
    }


def validate_with_ai(image_content: bytes, title: str, description: str, category: str = None, user_confirmed: bool = False) -> dict:
    """
    Validate complaint using AI model with INTELLIGENT confidence handling:
    
    CONFIDENCE TIERS:
    - HIGH (≥55%): Auto-approve if category matches
    - LOW (45-55%): Return "low-confidence" status, ask user confirmation
    - REJECT (<45%): Reject as unclear/irrelevant
    
    DYNAMIC THRESHOLDS per class (real-world images vary):
    - Garbage: 50% (often mixed backgrounds)
    - Pothole: 55% (can be subtle)
    - Waterlogging: 50% (reflections cause issues)
    - Invalid: 60% (need higher confidence to reject)
    
    If user_confirmed=True, accept low-confidence predictions.
    
    Args:
        category: Can be a single category or comma-separated list (e.g., "Garbage,Pothole")
    """
    # Parse multiple categories if provided
    user_categories = []
    if category:
        user_categories = [normalize_category(cat.strip()) for cat in category.split(",")]
        user_categories = [cat for cat in user_categories if cat]  # Remove None/empty
    
    # Dynamic thresholds per category
    THRESHOLDS = {
        'garbage': {'high': 0.55, 'low': 0.40},
        'pothole': {'high': 0.55, 'low': 0.40},
        'waterlogging': {'high': 0.50, 'low': 0.35},
        'invalid': {'high': 0.60, 'low': 0.45},
        'default': {'high': 0.55, 'low': 0.40}
    }
    
    # Absolute minimum - below this, always reject
    ABSOLUTE_MINIMUM = 0.35
    
    classifier = get_classifier()
    
    if not classifier or not image_content:
        logger.warning("No classifier available or no image provided")
        return {
            "is_valid": False,
            "decision": "NO_CLASSIFIER",
            "status": "error",
            "reason": "Image validation system is not available. Please try again later.",
            "suggested_category": None,
            "detected_category": None,
            "image_classification": None,
            "confidence": 0.0,
            "method": "error",
            "requires_confirmation": False
        }
    
    try:
        # ================================================================
        # STEP 1: Classify the image
        # ================================================================
        result = classifier.classify(image_content)
        
        raw_predicted = result.get("predicted_class", "unknown")
        confidence = result.get("confidence", 0.0)
        method = result.get("method", "unknown")
        all_probs = result.get("all_probabilities", {})
        secondary_issues = result.get("secondary_issues", [])  # NEW: Multiple issues
        
        # Normalize the image prediction
        image_category = normalize_category(raw_predicted)
        
        # Get thresholds for this category
        thresholds = THRESHOLDS.get(image_category, THRESHOLDS['default'])
        high_threshold = thresholds['high']
        low_threshold = thresholds['low']
        
        # Format multi-issue detection message
        multi_issue_msg = ""
        if secondary_issues:
            secondary_list = [f"{issue['category']} ({issue['confidence_percent']}%)" 
                            for issue in secondary_issues]
            multi_issue_msg = f" Also detected: {', '.join(secondary_list)}."
            logger.info(f"MULTI-ISSUE DETECTED: Primary={image_category} ({confidence:.1%}), Secondary={secondary_list}")
        
        logger.info(f"IMAGE CLASSIFICATION: '{raw_predicted}' -> '{image_category}' (confidence: {confidence:.1%}, thresholds: high={high_threshold:.0%}, low={low_threshold:.0%})")
        
        # ================================================================
        # STEP 2: Analyze the complaint text
        # ================================================================
        text_analysis = analyze_text_for_category(title, description)
        text_category = text_analysis['category']
        
        if not text_category and category:
            text_category = normalize_category(category)
            logger.info(f"Using user-selected category: {category} -> {text_category}")
        
        logger.info(f"TEXT ANALYSIS: category='{text_category}', keywords={text_analysis.get('matched_keywords', [])}")
        
        # ================================================================
        # RULE 1: ABSOLUTE REJECT - Below minimum threshold
        # ================================================================
        if confidence < ABSOLUTE_MINIMUM:
            logger.warning(f"REJECTED: Confidence {confidence:.1%} below absolute minimum {ABSOLUTE_MINIMUM:.0%}")
            return {
                "is_valid": False,
                "decision": "VERY_LOW_CONFIDENCE",
                "status": "rejected",
                "reason": f"The uploaded image is too unclear to identify. Please upload a clearer image showing the civic issue.",
                "suggested_category": None,
                "detected_category": display_category(image_category) if image_category else None,
                "image_classification": raw_predicted,
                "confidence": confidence,
                "method": method,
                "secondary_issues": secondary_issues,
                "requires_confirmation": False
            }
        
        # ================================================================
        # RULE 2: INVALID IMAGE - High confidence invalid detection
        # ================================================================
        if image_category == 'invalid' and confidence >= THRESHOLDS['invalid']['high']:
            logger.warning(f"REJECTED: Invalid/irrelevant image ({confidence:.1%})")
            return {
                "is_valid": False,
                "decision": "INVALID_IMAGE",
                "status": "rejected",
                "reason": f"The uploaded image does not contain a visible civic issue. Please upload an image clearly showing garbage, pothole, or waterlogging.",
                "suggested_category": None,
                "detected_category": "Invalid/Irrelevant",
                "image_classification": raw_predicted,
                "confidence": confidence,
                "method": method,
                "secondary_issues": secondary_issues,
                "requires_confirmation": False
            }
        
        # ================================================================
        # RULE 3: LOW CONFIDENCE - Ask for user confirmation
        # ================================================================
        if confidence < high_threshold and confidence >= low_threshold:
            # If user already confirmed, accept it
            if user_confirmed:
                logger.info(f"APPROVED (user confirmed): '{image_category}' ({confidence:.1%})")
                return {
                    "is_valid": True,
                    "decision": "VALID_CONFIRMED",
                    "status": "approved",
                    "reason": f"Image confirmed by user as {display_category(image_category)}.{multi_issue_msg}",
                    "suggested_category": display_category(image_category),
                    "detected_category": display_category(image_category),
                    "image_classification": raw_predicted,
                    "confidence": confidence,
                    "method": method,
                    "secondary_issues": secondary_issues,
                    "requires_confirmation": False
                }
            
            # Otherwise, ask for confirmation
            logger.info(f"LOW CONFIDENCE: Asking user confirmation for '{image_category}' ({confidence:.1%})")
            return {
                "is_valid": False,
                "decision": "LOW_CONFIDENCE",
                "status": "needs_confirmation",
                "reason": f"The image appears to show {display_category(image_category)}, but the quality is not ideal.{multi_issue_msg}",
                "suggestion": f"Is this image showing {display_category(image_category).lower()}?",
                "suggested_category": display_category(image_category),
                "detected_category": display_category(image_category),
                "image_classification": raw_predicted,
                "confidence": confidence,
                "method": method,
                "secondary_issues": secondary_issues,
                "requires_confirmation": True,
                "confirmation_prompt": f"The AI detected this as '{display_category(image_category)}' with {confidence:.1%} confidence. Is this correct?"
            }
        
        # ================================================================
        # RULE 4: CATEGORY MISMATCH - Text vs Image
        # ================================================================
        
        # Check if text category conflicts with BOTH image AND user selection
        if text_category and image_category and text_category != image_category and image_category != 'invalid':
            # IMPORTANT: If ANY user selection matches image, trust the image
            # Example: User selects "Garbage,Pothole", image shows "pothole", text mentions "garbage"
            # → This is OK, user knows what they're reporting
            if user_categories and image_category in user_categories and confidence >= high_threshold:
                # User selection matches image classification - trust this, ignore text keywords
                logger.info(f"Text mentions '{text_category}' but user selected '{category}' and image shows '{image_category}' - APPROVING")
                display_final = display_category(image_category)
                
                return {
                    "is_valid": True,
                    "decision": "VALID_USER_IMAGE_MATCH",
                    "status": "approved",
                    "reason": f"Image validated as {display_final} ({confidence:.1%} confidence).{multi_issue_msg}",
                    "suggested_category": display_final,
                    "detected_category": display_final,
                    "image_classification": raw_predicted,
                    "confidence": confidence,
                    "method": method,
                    "secondary_issues": secondary_issues,
                    "requires_confirmation": False
                }
            
            # Otherwise, there's a genuine mismatch (user didn't select, or selected something different)
            display_image = display_category(image_category)
            display_text = display_category(text_category)
            
            logger.warning(f"MISMATCH: Text='{text_category}' vs Image='{image_category}'")
            return {
                "is_valid": False,
                "decision": "CATEGORY_MISMATCH",
                "status": "mismatch",
                "reason": f"Your description does not match the image.",
                "suggestion": f"Your description mentions {display_text.lower()}, but the image shows {display_image.lower()}. Please ensure your description accurately describes the image.",
                "suggested_category": display_image,
                "detected_category": display_image,
                "expected_category": display_text,
                "image_classification": raw_predicted,
                "confidence": confidence,
                "method": method,
                "secondary_issues": secondary_issues,
                "user_category": display_text,
                "ai_category": display_image,
                "requires_confirmation": False
            }
        
        # ================================================================
        # RULE 5: HIGH CONFIDENCE VALID - Auto approve
        # ================================================================
        if image_category in ['garbage', 'pothole', 'waterlogging'] and confidence >= high_threshold:
            display_final = display_category(image_category)
            logger.info(f"APPROVED: '{image_category}' with high confidence ({confidence:.1%})")
            
            return {
                "is_valid": True,
                "decision": "VALID",
                "status": "approved",
                "reason": f"Image validated as {display_final} ({confidence:.1%} confidence).{multi_issue_msg}",
                "suggested_category": display_final,
                "detected_category": display_final,
                "image_classification": raw_predicted,
                "confidence": confidence,
                "method": method,
                "secondary_issues": secondary_issues,
                "requires_confirmation": False
            }
        
        # ================================================================
        # RULE 6: No text category but valid civic issue image
        # ================================================================
        if not text_category and image_category in ['garbage', 'pothole', 'waterlogging']:
            display_final = display_category(image_category)
            logger.info(f"APPROVED: No text category, using image '{image_category}' ({confidence:.1%})")
            
            return {
                "is_valid": True,
                "decision": "VALID",
                "status": "approved",
                "reason": f"Image detected as {display_final} ({confidence:.1%} confidence).{multi_issue_msg}",
                "suggested_category": display_final,
                "detected_category": display_final,
                "image_classification": raw_predicted,
                "confidence": confidence,
                "method": method,
                "secondary_issues": secondary_issues,
                "requires_confirmation": False
            }
        
        # ================================================================
        # FALLBACK: Unclear case - ask for confirmation
        # ================================================================
        logger.info(f"FALLBACK: Unclear classification, asking confirmation")
        return {
            "is_valid": False,
            "decision": "UNCLEAR",
            "status": "needs_confirmation",
            "reason": f"Unable to clearly identify the issue in the image.{multi_issue_msg}",
            "suggestion": f"The AI detected this as possibly {display_category(image_category) if image_category else 'unknown'}. Please confirm or upload a clearer image.",
            "suggested_category": display_category(image_category) if image_category else None,
            "detected_category": display_category(image_category) if image_category else None,
            "image_classification": raw_predicted,
            "confidence": confidence,
            "method": method,
            "secondary_issues": secondary_issues,
            "requires_confirmation": True
        }
        
    except Exception as e:
        logger.error(f"AI validation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "is_valid": False,
            "decision": "ERROR",
            "status": "error",
            "reason": f"Validation system encountered an error. Please try again.",
            "suggested_category": None,
            "detected_category": None,
            "image_classification": None,
            "confidence": 0.0,
            "method": "error",
            "requires_confirmation": False
        }


@router.post("/report", response_model=schemas.ComplaintResponse)
async def report_issue(
    title: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    category: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user_confirmed: Optional[str] = Form(None),  # "true" if user confirmed low-confidence prediction
    current_user: dict = Depends(auth.get_current_user)
):
    """Submit a new complaint with AI-based image verification"""
    
    image_url = None
    image_content = None
    ai_validation = None
    
    # Parse user_confirmed (comes as string from form)
    is_user_confirmed = user_confirmed and user_confirmed.lower() == "true"
    
    # 1. Generate Tracking ID first (needed for image filename)
    tracking_id = generate_tracking_id()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # 2. Read image if provided
    if image and image.filename:
        try:
            image_content = await image.read()
            logger.info(f"Image received: {image.filename}, size: {len(image_content)} bytes")
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            image_content = None
    
    # 3. AI Validation (if image provided)
    if image_content:
        logger.info(f"Validating complaint with AI: {title} (user_confirmed={is_user_confirmed})")
        ai_validation = validate_with_ai(image_content, title, description, category, is_user_confirmed)
        
        # Check validation status
        status = ai_validation.get("status", "error")
        decision = ai_validation.get("decision", "UNKNOWN")
        
        # If needs confirmation and user hasn't confirmed yet, return special response
        if status == "needs_confirmation" and not is_user_confirmed:
            error_detail = {
                "error": "NEEDS_CONFIRMATION",
                "status": "needs_confirmation",
                "message": ai_validation.get("reason"),
                "suggestion": ai_validation.get("suggestion"),
                "detected_category": ai_validation.get("detected_category"),
                "confidence": ai_validation.get("confidence"),
                "confirmation_prompt": ai_validation.get("confirmation_prompt"),
                "requires_confirmation": True
            }
            raise HTTPException(status_code=400, detail=error_detail)
        
        # If rejected (not needs_confirmation), return error
        if not ai_validation.get("is_valid", False) and status != "needs_confirmation":
            error_messages = {
                "INVALID_IMAGE": {
                    "error": "INVALID_IMAGE",
                    "status": "rejected",
                    "message": ai_validation.get("reason"),
                    "suggestion": "Please upload an image that clearly shows a civic issue (garbage, pothole, or waterlogging)."
                },
                "VERY_LOW_CONFIDENCE": {
                    "error": "VERY_LOW_CONFIDENCE",
                    "status": "rejected",
                    "message": ai_validation.get("reason"),
                    "suggestion": "The image is too unclear. Please upload a better quality image."
                },
                "CATEGORY_MISMATCH": {
                    "error": "CATEGORY_MISMATCH",
                    "status": "mismatch",
                    "message": ai_validation.get("reason"),
                    "suggestion": ai_validation.get("suggestion"),
                    "detected_category": ai_validation.get("detected_category"),
                    "expected_category": ai_validation.get("expected_category")
                },
                "NO_CLASSIFIER": {
                    "error": "NO_CLASSIFIER",
                    "status": "error",
                    "message": ai_validation.get("reason"),
                    "suggestion": "Please try again later."
                }
            }
            
            error_detail = error_messages.get(decision, {
                "error": decision,
                "status": "rejected",
                "message": ai_validation.get("reason", "Validation failed"),
                "suggestion": "Please upload a valid image showing the civic issue."
            })
            
            error_detail["detected_category"] = ai_validation.get("detected_category")
            error_detail["confidence"] = ai_validation.get("confidence")
            error_detail["requires_confirmation"] = False
            
            raise HTTPException(status_code=400, detail=error_detail)
    
    # 4. Upload image to Supabase Storage AFTER validation
    if image_content:
        try:
            # Format: complaint_<tracking_id>_<timestamp>.jpg
            file_extension = image.filename.split(".")[-1].lower() if "." in image.filename else "jpg"
            file_name = f"complaint_{tracking_id}_{timestamp}.{file_extension}"
            
            logger.info(f"Uploading image to Supabase Storage: {file_name}")
            
            # Upload to Supabase Storage
            upload_response = supabase.storage.from_(STORAGE_BUCKET).upload(
                path=file_name,
                file=image_content,
                file_options={"content-type": image.content_type or "image/jpeg"}
            )
            
            logger.info(f"Upload response: {upload_response}")
            
            # Get public URL
            image_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_name)
            logger.info(f"Image uploaded successfully. URL: {image_url}")
            
        except Exception as e:
            logger.error(f"Storage upload failed: {e}")
            # Try alternative upload method
            try:
                logger.info("Trying alternative upload method...")
                # Use upsert to overwrite if exists
                upload_response = supabase.storage.from_(STORAGE_BUCKET).upload(
                    path=file_name,
                    file=image_content,
                    file_options={"content-type": image.content_type or "image/jpeg", "upsert": "true"}
                )
                image_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_name)
                logger.info(f"Alternative upload successful. URL: {image_url}")
            except Exception as e2:
                logger.error(f"Alternative upload also failed: {e2}")
                image_url = None
    
    # 5. Extract geotag from image (lat_img, long_img) using OCR + EXIF
    lat_img = None
    long_img = None
    geo_source = None
    if image_content:
        try:
            extractor = get_geotag_extractor()
            if extractor:
                # Try the new OCR-enabled extractor (has extract_all method)
                if hasattr(extractor, 'extract_all'):
                    geotag_data = extractor.extract_all(image_content)
                else:
                    # Fallback to old EXIF-only method
                    geotag_data = extractor.extract_geotag(image_content)
                
                lat_img = geotag_data.get("lat_img")
                long_img = geotag_data.get("long_img")
                geo_source = geotag_data.get("source", "unknown")
                
                if lat_img and long_img:
                    logger.info(f"Extracted geotag from image via {geo_source}: lat={lat_img}, lon={long_img}")
                else:
                    logger.info("No geotag found in image (EXIF or OCR)")
        except Exception as e:
            logger.warning(f"Failed to extract geotag: {e}")
    
    # 6. Determine category (use AI suggestion if available, else user input, else default)
    # Category can now be comma-separated (e.g., "Garbage,Pothole")
    if ai_validation and ai_validation.get("suggested_category"):
        final_category = ai_validation["suggested_category"].capitalize()
    elif category:
        # Keep multiple categories if provided
        final_category = category  # e.g., "Garbage,Pothole" or "Garbage + Pothole"
    else:
        final_category = "General"
    
    # 7. Determine classification result
    classification_result = None
    if ai_validation:
        classification_result = ai_validation.get("image_classification", "general")
    
    # 8. Insert Complaint into Supabase
    now = datetime.utcnow().isoformat()
    new_complaint_data = {
        "tracking_id": tracking_id,
        "user_id": current_user["id"],
        "title": title,
        "description": description,
        "category": final_category,
        "classification_result": classification_result,
        "image_url": image_url,
        "latitude": latitude,
        "longitude": longitude,
        "lat_img": lat_img,
        "long_img": long_img,
        "status": "Pending",
        "created_at": now,
        "updated_at": now
    }
    
    try:
        response = supabase.table("complaints").insert(new_complaint_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save complaint")
        
        logger.info(f"Complaint saved: {tracking_id} - Category: {final_category}")
        return response.data[0]
    except Exception as db_error:
        logger.error(f"DB insert failed: {db_error}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")


@router.post("/validate-image")
async def validate_image_only(
    title: str = Form(...),
    description: str = Form(...),
    category: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Validate an image without submitting the complaint.
    Useful for preview/validation before submission.
    """
    if not image or not image.filename:
        raise HTTPException(status_code=400, detail="Image is required for validation")
    
    image_content = await image.read()
    
    # Run AI validation
    validation_result = validate_with_ai(image_content, title, description, category)
    
    return {
        "image_classification": validation_result.get("image_classification"),
        "classification_confidence": validation_result.get("classification_confidence", 0),
        "ocr_text": validation_result.get("ocr_text", ""),
        "decision": validation_result.get("decision"),
        "reason": validation_result.get("reason"),
        "is_valid": validation_result.get("is_valid", False),
        "suggested_category": validation_result.get("suggested_category")
    }

@router.get("/report/{tracking_id}", response_model=schemas.ComplaintResponse)
def get_complaint_by_tracking_id(tracking_id: str):
    """Get complaint status by tracking ID (public endpoint)"""
    response = supabase.table("complaints").select("*").eq("tracking_id", tracking_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return response.data[0]

@router.get("/user/reports", response_model=List[schemas.ComplaintResponse])
def get_user_reports(current_user: dict = Depends(auth.get_current_user)):
    """Get all complaints submitted by the current user"""
    response = supabase.table("complaints").select("*").eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
    
    return response.data if response.data else []

@router.get("/track/{tracking_id}")
def track_complaint(tracking_id: str):
    """Public endpoint to track complaint status with full details"""
    # Get complaint
    response = supabase.table("complaints").select("*").eq("tracking_id", tracking_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint = response.data[0]
    
    # Get admin logs for this complaint
    logs_response = supabase.table("admin_logs").select("message, timestamp").eq("complaint_id", complaint["id"]).order("timestamp", desc=True).execute()
    
    admin_logs = logs_response.data if logs_response.data else []
    
    return {
        "id": complaint["id"],
        "tracking_id": complaint["tracking_id"],
        "title": complaint.get("title"),
        "description": complaint["description"],
        "category": complaint["category"],
        "status": complaint["status"],
        "latitude": complaint["latitude"],
        "longitude": complaint["longitude"],
        "image_url": complaint.get("image_url"),
        "classification_result": complaint.get("classification_result"),
        "created_at": complaint["created_at"],
        "updated_at": complaint["updated_at"],
        "admin_logs": admin_logs
    }


@router.delete("/user/complaint/{complaint_id}")
async def delete_user_complaint(
    complaint_id: int,
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Delete a user's own complaint.
    Only allowed if complaint status is 'Pending'.
    Also deletes the associated image from Supabase Storage.
    """
    # First, get the complaint to verify ownership and status
    response = supabase.table("complaints").select("*").eq("id", complaint_id).eq("user_id", current_user["id"]).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found or you don't have permission to delete it")
    
    complaint = response.data[0]
    
    # Check if complaint can be deleted (only pending complaints)
    if complaint["status"] != "Pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete complaint. Status is '{complaint['status']}'. Only pending complaints can be deleted."
        )
    
    # Delete the image from Supabase Storage if exists
    if complaint.get("image_url"):
        try:
            # Extract filename from URL
            image_url = complaint["image_url"]
            # URL format: https://xxx.supabase.co/storage/v1/object/public/complaint-images/filename.jpg
            file_name = image_url.split("/")[-1]
            if file_name:
                supabase.storage.from_(STORAGE_BUCKET).remove([file_name])
                logger.info(f"Deleted image: {file_name}")
        except Exception as e:
            logger.warning(f"Could not delete image from storage: {e}")
    
    # Delete the complaint from database
    try:
        delete_response = supabase.table("complaints").delete().eq("id", complaint_id).execute()
        logger.info(f"Deleted complaint: {complaint['tracking_id']}")
        return {"message": "Complaint deleted successfully", "tracking_id": complaint["tracking_id"]}
    except Exception as e:
        logger.error(f"Failed to delete complaint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete complaint: {str(e)}")


# ============================================================================
# WORK COMPLETION VERIFICATION
# ============================================================================

@router.post("/complaints/{complaint_id}/verify-completion")
async def verify_work_completion(
    complaint_id: int,
    after_image: UploadFile = File(...),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Verify work completion by comparing before/after images.
    
    Flow:
    1. Fetch original complaint (before image)
    2. Download before image from storage
    3. Compare with uploaded after image
    4. Update complaint status if verified
    
    Args:
        complaint_id: ID of the complaint to verify
        after_image: Completion verification image (after work done)
        current_user: Authenticated user (admin/worker)
    
    Returns:
        Verification result with status, confidence, and details
    """
    logger.info(f"Verifying work completion for complaint {complaint_id}")
    
    # Fetch complaint
    try:
        complaint_response = supabase.table("complaints").select("*").eq("id", complaint_id).execute()
        if not complaint_response.data:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        complaint = complaint_response.data[0]
        logger.info(f"Found complaint: {complaint['tracking_id']}")
    except Exception as e:
        logger.error(f"Error fetching complaint: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching complaint: {str(e)}")
    
    # Check if complaint has an image
    if not complaint.get("image_url"):
        raise HTTPException(status_code=400, detail="Complaint has no before image for comparison")
    
    # Download before image from Supabase Storage
    try:
        before_image_url = complaint["image_url"]
        file_name = before_image_url.split("/")[-1]
        
        logger.info(f"Downloading before image: {file_name}")
        before_image_response = supabase.storage.from_(STORAGE_BUCKET).download(file_name)
        before_image_bytes = before_image_response
        
    except Exception as e:
        logger.error(f"Error downloading before image: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading before image: {str(e)}")
    
    # Read after image
    try:
        after_image_bytes = await after_image.read()
        logger.info(f"After image uploaded: {len(after_image_bytes)} bytes")
    except Exception as e:
        logger.error(f"Error reading after image: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading after image: {str(e)}")
    
    # Initialize verifier
    verifier = get_work_verifier()
    if not verifier:
        raise HTTPException(status_code=503, detail="Work verification service unavailable")
    
    # Run verification
    try:
        logger.info("Running AI verification...")
        verification_result = verifier.verify_completion(
            before_image=before_image_bytes,
            after_image=after_image_bytes,
            expected_issue=complaint.get("category", "").lower()
        )
        
        logger.info(f"Verification result: {verification_result['decision']}")
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
    # Upload after image to storage if verified
    after_image_url = None
    if verification_result['verified']:
        try:
            # Generate unique filename for after image
            after_file_name = f"{uuid.uuid4()}_after.jpg"
            
            # Upload to storage
            supabase.storage.from_(STORAGE_BUCKET).upload(
                after_file_name,
                after_image_bytes,
                {"content-type": after_image.content_type or "image/jpeg"}
            )
            
            # Get public URL
            after_image_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(after_file_name)
            logger.info(f"After image uploaded: {after_image_url}")
            
        except Exception as e:
            logger.warning(f"Could not upload after image: {e}")
            # Continue even if upload fails
    
    # Update complaint in database
    try:
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        if verification_result['verified']:
            update_data["status"] = "Resolved"
            if after_image_url:
                update_data["after_image_url"] = after_image_url
            update_data["verification_confidence"] = verification_result['confidence']
            update_data["verified_at"] = datetime.now().isoformat()
            update_data["verified_by"] = current_user["id"]
            
            logger.info(f"Marking complaint {complaint_id} as Resolved")
        else:
            logger.info(f"Complaint {complaint_id} verification failed: {verification_result['decision']}")
        
        # Update complaint
        supabase.table("complaints").update(update_data).eq("id", complaint_id).execute()
        
        # Add admin log
        if current_user.get("role") == "admin" or verification_result['verified']:
            log_message = f"Work verification: {verification_result['decision']} - {verification_result['message']}"
            supabase.table("admin_logs").insert({
                "complaint_id": complaint_id,
                "admin_id": current_user["id"],
                "message": log_message
            }).execute()
        
    except Exception as e:
        logger.error(f"Error updating complaint: {e}")
        # Don't fail the request if update fails - return verification result anyway
    
    # Return verification result
    return {
        "complaint_id": complaint_id,
        "tracking_id": complaint["tracking_id"],
        "verified": verification_result['verified'],
        "decision": verification_result['decision'],
        "confidence": verification_result['confidence'],
        "message": verification_result['message'],
        "details": verification_result.get('details', {}),
        "after_image_url": after_image_url,
        "status_updated": verification_result['verified']
    }
