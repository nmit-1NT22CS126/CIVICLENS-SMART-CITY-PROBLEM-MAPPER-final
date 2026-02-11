"""
CivicLens OCR and Geo-Extraction Module
========================================
Extracts:
1. GPS coordinates from image EXIF metadata
2. GPS text/stamps from image using OCR (pytesseract/easyocr)
3. Address text that might contain location info

Supports:
- EXIF GPS data extraction
- OCR-based coordinate detection (printed GPS on image)
- Regex patterns for lat/long formats
"""

import os
import io
import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import OCR libraries
OCR_AVAILABLE = False
TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    OCR_AVAILABLE = True
    logger.info("pytesseract available")
except ImportError:
    logger.warning("pytesseract not installed. OCR text extraction will be limited.")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
    OCR_AVAILABLE = True
    logger.info("easyocr available")
except ImportError:
    logger.warning("easyocr not installed. Using pytesseract only.")


class GeoExtractor:
    """
    Extracts geographic coordinates from images via:
    1. EXIF metadata (GPS tags)
    2. OCR text detection (printed GPS stamps)
    """
    
    # Regex patterns for GPS coordinates
    GPS_PATTERNS = [
        # Decimal degrees: 12.345678, 78.901234 or 12.345678° N, 78.901234° E
        r'(-?\d{1,3}\.\d{4,8})[°]?\s*[,\s]\s*(-?\d{1,3}\.\d{4,8})',
        
        # Lat/Long labeled: Lat: 12.3456 Long: 78.9012
        r'[Ll]at[itude]*[:\s]+(-?\d{1,3}\.\d{4,8})[°]?\s*[,\s]*[Ll]on[gitude]*[:\s]+(-?\d{1,3}\.\d{4,8})',
        
        # GPS format: GPS 12.3456, 78.9012
        r'GPS[:\s]+(-?\d{1,3}\.\d{4,8})[°]?\s*[,\s]\s*(-?\d{1,3}\.\d{4,8})',
        
        # DMS format: 12°34'56"N, 78°90'12"E
        r"(\d{1,3})[°]\s*(\d{1,2})[\'′]\s*(\d{1,2}(?:\.\d+)?)[\"″]?\s*([NSns])[,\s]+(\d{1,3})[°]\s*(\d{1,2})[\'′]\s*(\d{1,2}(?:\.\d+)?)[\"″]?\s*([EWew])",
        
        # Simple coordinate pair in text
        r'(\d{1,2}\.\d{5,7})\s*[,/]\s*(\d{2,3}\.\d{5,7})',
    ]
    
    def __init__(self):
        """Initialize the geo extractor."""
        self.easyocr_reader = None
        
        # Initialize EasyOCR if available (lazy loading)
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR reader initialized")
            except Exception as e:
                logger.warning(f"Could not initialize EasyOCR: {e}")
    
    def extract_all(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract all geographic data from image.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with lat_img, long_img, source, and raw_text
        """
        result = {
            "lat_img": None,
            "long_img": None,
            "source": None,
            "raw_text": None,
            "address_text": None,
            "has_geotag": False
        }
        
        # Method 1: Try EXIF extraction first (most reliable)
        exif_result = self.extract_from_exif(image_data)
        if exif_result.get("has_geotag"):
            result.update(exif_result)
            result["source"] = "exif"
            logger.info(f"GPS from EXIF: {result['lat_img']}, {result['long_img']}")
            return result
        
        # Method 2: Try OCR extraction
        if OCR_AVAILABLE:
            ocr_result = self.extract_from_ocr(image_data)
            if ocr_result.get("has_geotag"):
                result.update(ocr_result)
                result["source"] = "ocr"
                logger.info(f"GPS from OCR: {result['lat_img']}, {result['long_img']}")
                return result
            
            # Even if no GPS found, keep the raw text for address info
            if ocr_result.get("raw_text"):
                result["raw_text"] = ocr_result["raw_text"]
                result["address_text"] = self._extract_address(ocr_result["raw_text"])
        
        return result
    
    def extract_from_exif(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract GPS coordinates from image EXIF data.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with lat_img, long_img (or None if not found)
        """
        result = {"lat_img": None, "long_img": None, "has_geotag": False}
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Try multiple methods to get EXIF
            exif_data = None
            
            # Method 1: _getexif()
            try:
                exif_data = img._getexif()
            except AttributeError:
                pass
            
            # Method 2: getexif()
            if not exif_data:
                try:
                    exif_obj = img.getexif()
                    if exif_obj:
                        exif_data = dict(exif_obj)
                except Exception:
                    pass
            
            if not exif_data:
                logger.debug("No EXIF data found in image")
                return result
            
            # Find GPS info
            gps_info = {}
            GPS_INFO_TAG = 34853
            
            # Check tag 34853 (GPSInfo)
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
                return result
            
            # Extract latitude
            lat = self._convert_to_degrees(gps_info.get("GPSLatitude"))
            lat_ref = gps_info.get("GPSLatitudeRef", "N")
            if lat is not None and lat_ref == "S":
                lat = -lat
            
            # Extract longitude
            lon = self._convert_to_degrees(gps_info.get("GPSLongitude"))
            lon_ref = gps_info.get("GPSLongitudeRef", "E")
            if lon is not None and lon_ref == "W":
                lon = -lon
            
            # Validate coordinates
            if lat is not None and lon is not None:
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return {
                        "lat_img": round(lat, 6),
                        "long_img": round(lon, 6),
                        "has_geotag": True
                    }
            
            return result
            
        except Exception as e:
            logger.warning(f"Error extracting EXIF GPS: {e}")
            return result
    
    def extract_from_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract GPS coordinates from image text using OCR.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with lat_img, long_img, raw_text
        """
        result = {"lat_img": None, "long_img": None, "has_geotag": False, "raw_text": None}
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Try EasyOCR first (better for stamps/watermarks)
            text = ""
            
            if self.easyocr_reader:
                try:
                    # Save to temp buffer for easyocr
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='JPEG')
                    img_buffer.seek(0)
                    
                    results = self.easyocr_reader.readtext(img_buffer.getvalue())
                    text = " ".join([r[1] for r in results])
                    logger.debug(f"EasyOCR text: {text[:100]}...")
                except Exception as e:
                    logger.warning(f"EasyOCR failed: {e}")
            
            # Fallback to pytesseract
            if not text and TESSERACT_AVAILABLE:
                try:
                    text = pytesseract.image_to_string(img)
                    logger.debug(f"Tesseract text: {text[:100]}...")
                except Exception as e:
                    logger.warning(f"Tesseract failed: {e}")
            
            result["raw_text"] = text
            
            if not text:
                return result
            
            # Try to find GPS coordinates in text
            coords = self._parse_gps_from_text(text)
            if coords:
                result["lat_img"] = coords[0]
                result["long_img"] = coords[1]
                result["has_geotag"] = True
            
            return result
            
        except Exception as e:
            logger.warning(f"Error in OCR extraction: {e}")
            return result
    
    def _parse_gps_from_text(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Parse GPS coordinates from OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Tuple of (latitude, longitude) or None
        """
        if not text:
            return None
        
        # Clean text
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        for pattern in self.GPS_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    # Handle DMS format (8 groups)
                    if len(match) == 8:
                        lat = self._dms_to_decimal(
                            float(match[0]), float(match[1]), float(match[2]), match[3]
                        )
                        lon = self._dms_to_decimal(
                            float(match[4]), float(match[5]), float(match[6]), match[7]
                        )
                    else:
                        # Decimal format (2 groups)
                        lat = float(match[0])
                        lon = float(match[1])
                    
                    # Validate
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return (round(lat, 6), round(lon, 6))
                        
                except (ValueError, IndexError) as e:
                    continue
        
        return None
    
    def _dms_to_decimal(self, degrees: float, minutes: float, seconds: float, direction: str) -> float:
        """Convert DMS (degrees, minutes, seconds) to decimal degrees."""
        decimal = degrees + minutes / 60 + seconds / 3600
        if direction.upper() in ['S', 'W']:
            decimal = -decimal
        return decimal
    
    def _convert_to_degrees(self, value) -> Optional[float]:
        """Convert EXIF GPS format to decimal degrees."""
        if not value:
            return None
        
        try:
            def to_float(v):
                if v is None:
                    return 0.0
                if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                    return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
                elif isinstance(v, tuple) and len(v) == 2:
                    return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
                return float(v)
            
            if len(value) >= 3:
                d = to_float(value[0])
                m = to_float(value[1])
                s = to_float(value[2])
                return d + (m / 60.0) + (s / 3600.0)
            
            return None
        except Exception as e:
            logger.warning(f"Error converting GPS: {e}")
            return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract potential address from OCR text."""
        if not text:
            return None
        
        # Common address patterns
        address_patterns = [
            r'(?:Address|Location|Place)[:\s]+([^\n]+)',
            r'(?:Street|Road|Lane|Avenue|Nagar|Colony)[:\s]*([^\n]+)',
            r'\d+[,\s]+[A-Za-z\s]+(?:Street|Road|Lane|Ave|Nagar|Colony)',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.lastindex else match.group(0).strip()
        
        return None


# Singleton instance
_geo_extractor = None

def get_geo_extractor() -> GeoExtractor:
    """Get or create singleton GeoExtractor instance."""
    global _geo_extractor
    if _geo_extractor is None:
        _geo_extractor = GeoExtractor()
    return _geo_extractor


# Convenience function
def extract_geotag(image_data: bytes) -> Dict[str, Any]:
    """
    Extract geotag from image data.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dictionary with lat_img, long_img, source, etc.
    """
    return get_geo_extractor().extract_all(image_data)
