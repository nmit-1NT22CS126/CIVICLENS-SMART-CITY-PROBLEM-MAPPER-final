"""
CivicLens AI Verification System
Version 4.0 - Complete verification with:
- Image Classification (MobileNetV2 or EfficientNet-B3)
- Text Analysis & Understanding
- Image-Text Matching
- Geotag Extraction (EXIF + OCR)
- Dynamic Confidence Thresholds

Classes: Garbage, Potholes, Waterlogging, Invalid_data
"""

import os
import json
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import re
from typing import Tuple, Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Dynamic thresholds based on model type
CONFIDENCE_THRESHOLDS = {
    'efficientnet': 0.65,  # EfficientNet is more calibrated
    'mobilenet': 0.70,     # MobileNetV2 baseline
    'fallback': 0.50       # Heuristic fallback
}
DEFAULT_CONFIDENCE_THRESHOLD = 0.70

CATEGORIES = ['Garbage', 'Invalid_data', 'Potholes', 'water logging']
CIVIC_ISSUES = ['garbage', 'pothole', 'waterlogging']  # Valid civic issues (normalized)

# Model architecture detection
SUPPORTED_MODELS = ['efficientnet', 'mobilenet']

# Category keywords for text analysis
CATEGORY_KEYWORDS = {
    'garbage': [
        'garbage', 'trash', 'waste', 'rubbish', 'dump', 'litter', 'dirty',
        'debris', 'refuse', 'junk', 'pollution', 'bin', 'overflow', 'pile',
        'mess', 'filth', 'sanitation', 'hygiene', 'stink', 'smell', 'rot',
        'dustbin', 'garbage dump', 'waste pile', 'littering', 'plastic',
        'scrap', 'disposal', 'sewage smell', 'unhygienic', 'cleanliness'
    ],
    'pothole': [
        'pothole', 'hole', 'pit', 'crater', 'road', 'damage', 'crack', 
        'broken', 'pavement', 'asphalt', 'street', 'highway', 'cavity',
        'dent', 'depression', 'roadway', 'surface', 'tar', 'road damage',
        'broken road', 'road hole', 'street damage', 'road repair',
        'uneven road', 'road condition', 'bumpy road', 'damaged road'
    ],
    'waterlogging': [
        'water', 'flood', 'waterlog', 'drain', 'clog', 'overflow', 'sewage',
        'puddle', 'stagnant', 'blockage', 'drainage', 'rain', 'submerge',
        'waterlogging', 'flooded', 'water logging', 'standing water',
        'water accumulation', 'drainage issue', 'blocked drain', 'flooding',
        'rainwater', 'water stagnation', 'wet road', 'water on road'
    ]
}


class ImageClassifier:
    """
    CNN-based image classifier for civic issue detection.
    Supports both MobileNetV2 and EfficientNet-B3 architectures.
    Automatically detects model type and applies appropriate preprocessing.
    """
    
    def __init__(self, model_path: str = None):
        """Initialize the classifier."""
        self.model = None
        self.model_type = 'mobilenet'  # Default model type
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        
        # Priority order for model loading
        self.model_paths = [
            ('efficientnet', os.path.join(self.models_dir, 'efficientnet_civic_classifier.keras')),
            ('efficientnet', os.path.join(self.models_dir, 'efficientnet_civic_classifier.h5')),
            ('efficientnet', os.path.join(self.models_dir, 'final_pipeline.keras')),
            ('efficientnet', os.path.join(self.models_dir, 'final_pipeline.h5')),
            ('mobilenet', os.path.join(self.models_dir, 'civic_classifier.keras')),
            ('mobilenet', os.path.join(self.models_dir, 'civic_classifier.h5')),
        ]
        
        if model_path:
            # Detect model type from path
            if 'efficientnet' in model_path.lower() or 'final_pipeline' in model_path.lower():
                self.model_paths.insert(0, ('efficientnet', model_path))
            else:
                self.model_paths.insert(0, ('mobilenet', model_path))
        
        self.class_names_path = os.path.join(self.models_dir, 'class_names.json')
        self.categories = self._load_class_names()
        self.img_size = (224, 224)  # Both models use 224x224
        self.confidence_threshold = DEFAULT_CONFIDENCE_THRESHOLD
        self._load_model()
    
    def _load_class_names(self):
        """Load class names from JSON file."""
        try:
            if os.path.exists(self.class_names_path):
                with open(self.class_names_path, 'r') as f:
                    class_names = json.load(f)
                if isinstance(class_names, dict):
                    return [class_names[str(i)] for i in range(len(class_names))]
                return class_names
        except Exception as e:
            logger.warning(f"Could not load class names: {e}")
        return CATEGORIES
    
    def _load_model(self):
        """Load the trained model (tries EfficientNet first, then MobileNet)."""
        try:
            import tensorflow as tf
            from tensorflow.keras.models import load_model
            
            for model_type, model_path in self.model_paths:
                if os.path.exists(model_path):
                    logger.info(f"Loading {model_type} model from {model_path}")
                    try:
                        self.model = load_model(model_path)
                        self.model_type = model_type
                        self.confidence_threshold = CONFIDENCE_THRESHOLDS.get(model_type, DEFAULT_CONFIDENCE_THRESHOLD)
                        logger.info(f"Model loaded successfully! Type: {model_type}, Classes: {self.categories}")
                        logger.info(f"Confidence threshold: {self.confidence_threshold:.0%}")
                        return
                    except Exception as e:
                        logger.warning(f"Could not load {model_path}: {e}")
                        continue
            
            logger.warning("No trained model found. Classifier will use fallback method.")
            self.model = None
            self.confidence_threshold = CONFIDENCE_THRESHOLDS['fallback']
            
        except ImportError as e:
            logger.error(f"TensorFlow not installed: {e}")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """
        Preprocess image for model input.
        Applies appropriate preprocessing based on model type.
        """
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.resize(self.img_size, Image.Resampling.LANCZOS)
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Apply model-specific preprocessing
        if self.model_type == 'efficientnet':
            from tensorflow.keras.applications.efficientnet import preprocess_input
            img_array = preprocess_input(img_array)
        else:  # mobilenet
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
            img_array = preprocess_input(img_array)
        
        return img_array
    
    def classify(self, image_data) -> Dict[str, Any]:
        """
        Classify an image into civic issue categories.
        
        Args:
            image_data: Raw image bytes OR file path string
            
        Returns:
            Dictionary with classification results
        """
        # Handle file path input
        if isinstance(image_data, str):
            try:
                with open(image_data, 'rb') as f:
                    image_data = f.read()
            except Exception as e:
                logger.error(f"Could not read file {image_data}: {e}")
                return {
                    "predicted_class": "invalid",
                    "confidence": 0.0,
                    "is_civic_issue": False,
                    "method": "error"
                }
        
        if self.model is None:
            return self._fallback_classify(image_data)
        
        try:
            img_array = self.preprocess_image(image_data)
            predictions = self.model.predict(img_array, verbose=0)
            
            pred_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][pred_idx])
            predicted_class = self.categories[pred_idx]
            
            class_probs = {
                cat: float(prob) 
                for cat, prob in zip(self.categories, predictions[0])
            }
            
            normalized_class = self._normalize_class_name(predicted_class)
            is_civic_issue = normalized_class in CIVIC_ISSUES
            
            # Multi-issue detection: Find secondary issues above threshold
            secondary_issues = self._detect_secondary_issues(predictions[0], pred_idx)
            
            return {
                "predicted_class": normalized_class,
                "original_class": predicted_class,
                "confidence": confidence,
                "is_civic_issue": is_civic_issue,
                "all_probabilities": class_probs,
                "secondary_issues": secondary_issues,  # NEW: Multiple issue detection
                "method": "trained_cnn_model"
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._fallback_classify(image_data)
    
    def _detect_secondary_issues(self, predictions: np.ndarray, primary_idx: int, 
                                 threshold: float = 0.30) -> List[Dict[str, Any]]:
        """
        Detect secondary civic issues in the image.
        
        Args:
            predictions: Model prediction probabilities array
            primary_idx: Index of the primary (highest) prediction
            threshold: Minimum confidence to consider as secondary issue (default: 30%)
            
        Returns:
            List of secondary issues with confidence scores
        """
        secondary = []
        
        for idx, prob in enumerate(predictions):
            # Skip primary prediction and invalid category
            if idx == primary_idx:
                continue
            
            normalized_name = self._normalize_class_name(self.categories[idx])
            
            # Only include civic issues (not "invalid") above threshold
            if normalized_name in CIVIC_ISSUES and float(prob) >= threshold:
                secondary.append({
                    "category": normalized_name,
                    "confidence": float(prob),
                    "confidence_percent": round(float(prob) * 100, 2)
                })
        
        # Sort by confidence (highest first)
        secondary.sort(key=lambda x: x['confidence'], reverse=True)
        
        return secondary
    
    def _normalize_class_name(self, class_name: str) -> str:
        """Normalize class names for API consistency."""
        name_map = {
            'Garbage': 'garbage',
            'Potholes': 'pothole',
            'water logging': 'waterlogging',
            'water_logging': 'waterlogging',
            'waterlogging': 'waterlogging',
            'Invalid_data': 'invalid',
            'invalid_data': 'invalid',
            'Invalid': 'invalid'
        }
        return name_map.get(class_name, class_name.lower())
    
    def _fallback_classify(self, image_data: bytes) -> Dict[str, Any]:
        """Fallback classification using image analysis heuristics."""
        try:
            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img)
            mean_colors = np.mean(img_array, axis=(0, 1))
            std_colors = np.std(img_array, axis=(0, 1))
            
            r, g, b = mean_colors
            
            if b > r and b > g and np.mean(std_colors) < 50:
                predicted = "waterlogging"
                confidence = 0.6
            elif r < 100 and g < 100 and b < 100:
                predicted = "pothole"
                confidence = 0.5
            elif np.mean(std_colors) > 60:
                predicted = "garbage"
                confidence = 0.5
            else:
                predicted = "invalid"
                confidence = 0.4
            
            return {
                "predicted_class": predicted,
                "confidence": confidence,
                "is_civic_issue": predicted in CIVIC_ISSUES,
                "all_probabilities": {cat: 0.25 for cat in self.categories},
                "method": "heuristic_fallback"
            }
            
        except Exception as e:
            logger.error(f"Fallback classification error: {e}")
            return {
                "predicted_class": "invalid",
                "confidence": 0.0,
                "is_civic_issue": False,
                "method": "error"
            }


class TextAnalyzer:
    """
    Analyzes complaint text to understand the user's intended category.
    Uses keyword matching and semantic understanding.
    """
    
    def __init__(self):
        self.keywords = CATEGORY_KEYWORDS
    
    def analyze(self, title: str, description: str) -> Dict[str, Any]:
        """
        Analyze complaint text to determine the intended category.
        
        Args:
            title: Complaint title
            description: Complaint description
            
        Returns:
            Dictionary with text analysis results
        """
        text = f"{title} {description}".lower()
        
        # Count keyword matches for each category
        scores = {}
        matched_keywords = {}
        
        for category, keywords in self.keywords.items():
            matches = []
            for keyword in keywords:
                if keyword.lower() in text:
                    matches.append(keyword)
            scores[category] = len(matches)
            matched_keywords[category] = matches
        
        # Determine predicted category
        max_score = max(scores.values()) if scores else 0
        
        if max_score == 0:
            return {
                "predicted_category": None,
                "confidence": 0.0,
                "scores": scores,
                "matched_keywords": matched_keywords,
                "method": "keyword_analysis"
            }
        
        # Get category with highest score
        predicted = max(scores, key=scores.get)
        
        # Calculate confidence based on number of matches
        confidence = min(1.0, max_score / 3.0)  # 3+ matches = 100% confidence
        
        return {
            "predicted_category": predicted,
            "confidence": confidence,
            "scores": scores,
            "matched_keywords": matched_keywords,
            "method": "keyword_analysis"
        }
    
    def extract_category_from_text(self, text: str) -> Optional[str]:
        """Extract explicit category mention from text."""
        text_lower = text.lower()
        
        # Direct mentions
        if any(word in text_lower for word in ['garbage', 'trash', 'waste', 'litter', 'dump']):
            return 'garbage'
        if any(word in text_lower for word in ['pothole', 'road damage', 'road hole', 'broken road']):
            return 'pothole'
        if any(word in text_lower for word in ['waterlogging', 'water logging', 'flood', 'water on road', 'standing water']):
            return 'waterlogging'
        
        return None


class GeotagExtractor:
    """
    Extracts GPS coordinates from image EXIF metadata.
    Handles various EXIF formats from different cameras/phones.
    """
    
    @staticmethod
    def extract_geotag(image_data: bytes) -> Dict[str, Any]:
        """
        Extract GPS coordinates from image EXIF data.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with lat_img, long_img (or None if not found)
            
        Note: Many images (especially those resaved, shared via apps, or 
        screenshots) do not contain GPS EXIF data. This is normal.
        """
        result = {"lat_img": None, "long_img": None, "has_geotag": False}
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Method 1: Try _getexif() - works for most JPEG images
            exif_data = None
            try:
                exif_data = img._getexif()
            except AttributeError:
                pass
            
            # Method 2: Try getexif() for newer Pillow versions
            if not exif_data:
                try:
                    exif_data = img.getexif()
                    if exif_data:
                        # Convert to dict format
                        exif_data = dict(exif_data)
                except Exception:
                    pass
            
            if not exif_data:
                logger.debug("No EXIF data found in image (this is common for resaved/shared images)")
                return result
            
            # Find GPS info - it's stored under tag 34853 (GPSInfo)
            gps_info = {}
            GPS_INFO_TAG = 34853
            
            # Check if GPSInfo is directly available
            if GPS_INFO_TAG in exif_data:
                gps_data = exif_data[GPS_INFO_TAG]
                if isinstance(gps_data, dict):
                    for gps_tag_id, gps_value in gps_data.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag] = gps_value
            
            # Also check by tag name
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo" and isinstance(value, dict):
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag] = gps_value
            
            if not gps_info:
                logger.debug("No GPS info found in EXIF data")
                return result
            
            logger.info(f"GPS info found: {list(gps_info.keys())}")
            
            # Extract latitude
            lat = GeotagExtractor._convert_to_degrees(gps_info.get("GPSLatitude"))
            lat_ref = gps_info.get("GPSLatitudeRef", "N")
            if lat is not None and lat_ref == "S":
                lat = -lat
            
            # Extract longitude
            lon = GeotagExtractor._convert_to_degrees(gps_info.get("GPSLongitude"))
            lon_ref = gps_info.get("GPSLongitudeRef", "E")
            if lon is not None and lon_ref == "W":
                lon = -lon
            
            # Validate coordinates are in reasonable range
            if lat is not None and lon is not None:
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    logger.info(f"Successfully extracted geotag: lat={lat:.6f}, lon={lon:.6f}")
                    return {
                        "lat_img": round(lat, 6),
                        "long_img": round(lon, 6),
                        "has_geotag": True
                    }
                else:
                    logger.warning(f"Invalid GPS coordinates: lat={lat}, lon={lon}")
            
            return result
            
        except Exception as e:
            logger.warning(f"Error extracting geotag: {e}")
            return result
    
    @staticmethod
    def _convert_to_degrees(value) -> Optional[float]:
        """Convert GPS coordinates from EXIF format to decimal degrees."""
        if not value:
            return None
        
        try:
            def to_float(v):
                """Convert various EXIF number formats to float."""
                if v is None:
                    return 0.0
                # Handle IFDRational (Pillow's rational number type)
                if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                    return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
                # Handle tuple format (numerator, denominator)
                elif isinstance(v, tuple) and len(v) == 2:
                    return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
                # Handle direct float/int
                return float(v)
            
            # GPS coordinates are stored as (degrees, minutes, seconds)
            if len(value) >= 3:
                d = to_float(value[0])  # degrees
                m = to_float(value[1])  # minutes
                s = to_float(value[2])  # seconds
                
                return d + (m / 60.0) + (s / 3600.0)
            
            return None
        except Exception as e:
            logger.warning(f"Error converting GPS coordinates: {e}")
            return None


class ComplaintVerifier:
    """
    Main verification class that combines image classification,
    text analysis, and matching logic.
    """
    
    def __init__(self):
        self.classifier = ImageClassifier()
        self.text_analyzer = TextAnalyzer()
        self.geotag_extractor = GeotagExtractor()
    
    def verify(self, image_data: bytes, title: str, description: str, 
               user_category: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete verification of a complaint.
        
        Args:
            image_data: Raw image bytes
            title: Complaint title
            description: Complaint description
            user_category: User-selected category (optional)
            
        Returns:
            Comprehensive verification result
        """
        result = {
            "is_valid": False,
            "decision": "PENDING",
            "message": "",
            "suggestion": "",
            "image_classification": None,
            "text_analysis": None,
            "geotag": None,
            "confidence": 0.0,
            "final_category": None
        }
        
        # Step 1: Classify the image
        logger.info("Step 1: Classifying image...")
        image_result = self.classifier.classify(image_data)
        result["image_classification"] = image_result
        
        image_category = image_result["predicted_class"]
        image_confidence = image_result["confidence"]
        
        logger.info(f"Image classified as: {image_category} ({image_confidence:.1%})")
        
        # Step 2: Analyze the complaint text
        logger.info("Step 2: Analyzing complaint text...")
        text_result = self.text_analyzer.analyze(title, description)
        result["text_analysis"] = text_result
        
        text_category = text_result["predicted_category"]
        
        # Use user-selected category if text analysis fails
        if not text_category and user_category:
            text_category = self._normalize_category(user_category)
            text_result["predicted_category"] = text_category
            text_result["method"] = "user_selection"
        
        logger.info(f"Text category: {text_category}")
        
        # Step 3: Extract geotag from image
        logger.info("Step 3: Extracting geotag...")
        geotag_result = self.geotag_extractor.extract_geotag(image_data)
        result["geotag"] = geotag_result
        
        # Step 4: Apply verification rules
        logger.info("Step 4: Applying verification rules...")
        
        # Rule 1: Check if image is invalid/irrelevant
        if image_category == "invalid" or image_category == "invalid_data":
            result["is_valid"] = False
            result["decision"] = "INVALID_IMAGE"
            result["message"] = "The uploaded image does not show a valid civic issue."
            result["suggestion"] = "Please upload a clear image showing the actual civic issue (garbage, pothole, or waterlogging)."
            result["confidence"] = image_confidence
            return result
        
        # Rule 2: Check confidence threshold (dynamic based on model)
        confidence_threshold = self.classifier.confidence_threshold
        if image_confidence < confidence_threshold:
            result["is_valid"] = False
            result["decision"] = "LOW_CONFIDENCE"
            result["message"] = f"The image quality or content is not clear enough. AI confidence: {image_confidence:.1%}"
            result["suggestion"] = "Please upload a clearer, well-lit image that prominently shows the civic issue."
            result["confidence"] = image_confidence
            return result
        
        # Rule 3: Check text-image category match
        if text_category and text_category != image_category:
            # Category mismatch!
            display_image_cat = self._display_category(image_category)
            display_text_cat = self._display_category(text_category)
            
            result["is_valid"] = False
            result["decision"] = "CATEGORY_MISMATCH"
            result["message"] = f"The image you uploaded is detected as '{display_image_cat}', but your complaint describes '{display_text_cat}'."
            result["suggestion"] = f"Please upload an image showing {display_text_cat.lower()}, or update your complaint description to match the image."
            result["confidence"] = image_confidence
            result["detected_category"] = display_image_cat
            result["expected_category"] = display_text_cat
            return result
        
        # All validations passed!
        result["is_valid"] = True
        result["decision"] = "APPROVED"
        result["message"] = f"Complaint verified successfully. Category: {self._display_category(image_category)}"
        result["suggestion"] = ""
        result["confidence"] = image_confidence
        result["final_category"] = self._display_category(image_category)
        
        return result
    
    def _normalize_category(self, category: str) -> str:
        """Normalize user category to match our internal categories."""
        if not category:
            return None
        
        category_lower = category.lower().strip()
        
        mappings = {
            'garbage': 'garbage',
            'trash': 'garbage',
            'waste': 'garbage',
            'pothole': 'pothole',
            'potholes': 'pothole',
            'road damage': 'pothole',
            'waterlogging': 'waterlogging',
            'water logging': 'waterlogging',
            'flooding': 'waterlogging',
            'flood': 'waterlogging',
            'other': None  # "Other" category should rely on text analysis
        }
        
        return mappings.get(category_lower, category_lower)
    
    def _display_category(self, category: str) -> str:
        """Convert internal category to display name."""
        display_names = {
            'garbage': 'Garbage',
            'pothole': 'Pothole',
            'waterlogging': 'Waterlogging',
            'invalid': 'Invalid/Unrelated'
        }
        return display_names.get(category, category.capitalize())


# Singleton instances for lazy loading
_classifier = None
_verifier = None


def get_classifier() -> ImageClassifier:
    """Get or create the singleton classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = ImageClassifier()
    return _classifier


def get_verifier() -> ComplaintVerifier:
    """Get or create the singleton verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = ComplaintVerifier()
    return _verifier
