# CivicLens ML Module
# Image Classification, OCR Geo-Extraction, and Complaint Verification

from .classifier import (
    ImageClassifier, 
    TextAnalyzer,
    GeotagExtractor, 
    ComplaintVerifier,
    get_classifier, 
    get_verifier,
    CONFIDENCE_THRESHOLDS,
    DEFAULT_CONFIDENCE_THRESHOLD
)
from .ocr_geo import GeoExtractor, get_geo_extractor, extract_geotag

__all__ = [
    'ImageClassifier', 
    'TextAnalyzer',
    'GeotagExtractor',  # EXIF-based extraction (from classifier.py)
    'GeoExtractor',     # Full extraction with OCR (from ocr_geo.py)
    'ComplaintVerifier',
    'get_classifier', 
    'get_verifier',
    'get_geo_extractor',
    'extract_geotag',
    'CONFIDENCE_THRESHOLDS',
    'DEFAULT_CONFIDENCE_THRESHOLD'
]
