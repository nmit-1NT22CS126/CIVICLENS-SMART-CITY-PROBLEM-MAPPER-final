"""
CivicLens Work Completion Verifier
===================================
Compares before/after images to verify if civic work was completed.

Uses:
1. MobileNetV2 feature extraction (location similarity)
2. Image classification (issue resolved?)
3. Visual difference detection

Workflow:
- Before: User's complaint image (e.g., pothole)
- After: Worker's completion image (e.g., fixed road)
- Verify: Same location + Issue resolved
"""

import os
import sys
import numpy as np
from typing import Dict, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("CIVICLENS WORK COMPLETION VERIFIER".center(80))
print("=" * 80)

# Import dependencies
print("\n[1/2] Loading dependencies...")
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
from PIL import Image
import io
import json

print("✓ Dependencies loaded")

# ============================================================================
# CONFIGURATION
# ============================================================================
# Get absolute path to model files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, 'models', 'civic_classifier.keras')
CLASS_NAMES_PATH = os.path.join(SCRIPT_DIR, 'models', 'class_names.json')

# Similarity thresholds
LOCATION_SIMILARITY_THRESHOLD = 0.60  # 60% similar = same location (relaxed from 70%)
SIGNIFICANT_CHANGE_THRESHOLD = 0.50   # <50% similar = significant change

# Issue categories
CIVIC_ISSUES = ['garbage', 'pothole', 'waterlogging', 'potholes']
RESOLVED_CATEGORIES = ['invalid_data', 'invalid']  # Normal/fixed state


class WorkCompletionVerifier:
    """
    Verifies if civic work was completed by comparing before/after images.
    """
    
    def __init__(self, model_path: str = MODEL_PATH):
        """Initialize the verifier."""
        print("\n[2/2] Loading model...")
        
        # Load classification model
        self.model = load_model(model_path)
        print(f"✓ Model loaded: {self.model.name}")
        
        # Create feature extractor (remove classification layers)
        # Use the global average pooling layer output for feature extraction
        feature_layer_name = None
        for layer in reversed(self.model.layers):
            if 'global' in layer.name.lower() and 'pooling' in layer.name.lower():
                feature_layer_name = layer.name
                break
        
        if feature_layer_name:
            self.feature_extractor = Model(
                inputs=self.model.input,
                outputs=self.model.get_layer(feature_layer_name).output
            )
            print(f"✓ Feature extractor created using layer: {feature_layer_name}")
        else:
            # Fallback: use second-to-last layer
            self.feature_extractor = Model(
                inputs=self.model.input,
                outputs=self.model.layers[-2].output
            )
            print(f"✓ Feature extractor created using layer: {self.model.layers[-2].name}")
        
        # Load class names
        with open(CLASS_NAMES_PATH, 'r') as f:
            class_names_dict = json.load(f)
            self.class_names = [class_names_dict[str(i)] for i in range(len(class_names_dict))]
        
        print(f"✓ Classes: {self.class_names}")
        print("=" * 80)
    
    def preprocess_image(self, img_data: bytes) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Args:
            img_data: Raw image bytes
            
        Returns:
            Preprocessed image array (1, 224, 224, 3)
        """
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to model input size
        img = img.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Convert to array
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Apply MobileNetV2 preprocessing
        img_array = preprocess_input(img_array)
        
        return img_array
    
    def extract_features(self, img_data: bytes) -> np.ndarray:
        """
        Extract feature vector from image.
        
        Args:
            img_data: Raw image bytes
            
        Returns:
            Feature vector (flattened)
        """
        img_array = self.preprocess_image(img_data)
        features = self.feature_extractor.predict(img_array, verbose=0)
        
        # Flatten to 1D vector
        return features.flatten()
    
    def classify_image(self, img_data: bytes) -> Dict[str, Any]:
        """
        Classify image using the trained model.
        
        Args:
            img_data: Raw image bytes
            
        Returns:
            Dictionary with predicted class and confidence
        """
        img_array = self.preprocess_image(img_data)
        predictions = self.model.predict(img_array, verbose=0)
        
        pred_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][pred_idx])
        predicted_class = self.class_names[pred_idx]
        
        # Normalize class name
        normalized_class = self._normalize_class_name(predicted_class)
        
        return {
            'class': normalized_class,
            'original_class': predicted_class,
            'confidence': confidence,
            'all_probabilities': {
                self.class_names[i]: float(predictions[0][i]) 
                for i in range(len(self.class_names))
            }
        }
    
    def _normalize_class_name(self, class_name: str) -> str:
        """Normalize class names for consistency."""
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
    
    def _check_surface_quality(self, img_data: bytes) -> Dict[str, float]:
        """
        Additional heuristic check for surface quality.
        Helps reduce false positives from shadows/textures.
        
        Returns:
            Dictionary with quality metrics
        """
        try:
            img = Image.open(io.BytesIO(img_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize for analysis
            img_small = img.resize((224, 224), Image.Resampling.LANCZOS)
            img_array = np.array(img_small, dtype=np.float32)
            
            # Convert to grayscale for edge detection
            gray = np.mean(img_array, axis=2)
            
            # Calculate edge intensity (potholes have strong edges)
            edges_x = np.abs(np.diff(gray, axis=1))
            edges_y = np.abs(np.diff(gray, axis=0))
            edge_intensity = (np.mean(edges_x) + np.mean(edges_y)) / 2.0
            
            # Calculate brightness uniformity (clean surfaces are more uniform)
            brightness_std = float(np.std(gray))
            brightness_mean = float(np.mean(gray))
            
            # Smooth surface score (higher = smoother/cleaner)
            # If edge intensity is low AND brightness is uniform, likely clean
            smoothness_score = 1.0 / (1.0 + float(edge_intensity) * 0.05)  # Less strict (was 0.1)
            uniformity_score = 1.0 / (1.0 + brightness_std * 0.005)  # Less strict (was 0.01)
            
            # Combined quality score (0-1, higher = cleaner surface)
            quality_score = (smoothness_score * 0.4 + uniformity_score * 0.6)
            
            return {
                'quality_score': float(quality_score),
                'edge_intensity': float(edge_intensity),
                'brightness_std': brightness_std,
                'brightness_mean': brightness_mean,
                'is_likely_clean': bool(quality_score > 0.60)  # LOWERED threshold from 0.65 to 0.60
            }
        except Exception as e:
            logger.error(f"Error in surface quality check: {e}")
            # Return default values if check fails
            return {
                'quality_score': 0.5,
                'edge_intensity': 0.0,
                'brightness_std': 0.0,
                'brightness_mean': 128.0,
                'is_likely_clean': False
            }
    
    def calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two feature vectors.
        
        Args:
            features1: First feature vector
            features2: Second feature vector
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Cosine similarity
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Convert from [-1, 1] to [0, 1]
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    def verify_completion(
        self, 
        before_image: bytes, 
        after_image: bytes,
        expected_issue: str = None
    ) -> Dict[str, Any]:
        """
        Verify if work was completed by comparing before/after images.
        
        Args:
            before_image: Original complaint image bytes
            after_image: Completion verification image bytes
            expected_issue: Expected issue type from complaint (optional)
            
        Returns:
            Comprehensive verification result
        """
        result = {
            'verified': False,
            'confidence': 0.0,
            'decision': 'PENDING',
            'message': '',
            'details': {}
        }
        
        print("\n" + "─" * 80)
        print("VERIFICATION IN PROGRESS")
        print("─" * 80)
        
        # Step 1: Extract features for location verification
        print("\n[Step 1/4] Extracting image features...")
        before_features = self.extract_features(before_image)
        after_features = self.extract_features(after_image)
        print(f"✓ Feature vectors extracted (size: {before_features.shape[0]})")
        
        # Step 2: Calculate location similarity
        print("\n[Step 2/4] Calculating location similarity...")
        location_similarity = self.calculate_similarity(before_features, after_features)
        result['details']['location_similarity'] = location_similarity
        print(f"✓ Location similarity: {location_similarity:.2%}")
        
        # Step 3: Classify both images
        print("\n[Step 3/4] Classifying images...")
        before_class = self.classify_image(before_image)
        after_class = self.classify_image(after_image)
        
        result['details']['before_classification'] = before_class
        result['details']['after_classification'] = after_class
        
        print(f"  Before: {before_class['original_class']} ({before_class['confidence']:.1%})")
        print(f"  After:  {after_class['original_class']} ({after_class['confidence']:.1%})")
        
        # Step 4: Analyze surface quality (heuristic check)
        print("\n[Step 4/5] Analyzing surface quality...")
        after_quality = self._check_surface_quality(after_image)
        result['details']['after_quality'] = after_quality
        print(f"  Quality score: {after_quality['quality_score']:.3f}")
        print(f"  Edge intensity: {after_quality['edge_intensity']:.2f}")
        print(f"  Brightness std: {after_quality['brightness_std']:.2f}")
        print(f"  Surface appears clean: {after_quality['is_likely_clean']}")
        
        # Step 5: Apply verification logic
        print("\n[Step 5/5] Applying verification rules...")
        
        # Rule 1: Check location match
        if location_similarity < LOCATION_SIMILARITY_THRESHOLD:
            result['verified'] = False
            result['decision'] = 'REJECTED_LOCATION'
            result['message'] = f"Images appear to be from different locations (similarity: {location_similarity:.1%})"
            result['confidence'] = location_similarity
            print(f"✗ Location mismatch (threshold: {LOCATION_SIMILARITY_THRESHOLD:.0%})")
            return result
        
        print(f"✓ Location verified (similarity: {location_similarity:.1%})")
        
        # Rule 2: Check if before image shows a civic issue
        if expected_issue:
            before_issue = expected_issue.lower()
        else:
            before_issue = before_class['class']
        
        if before_issue not in CIVIC_ISSUES:
            result['verified'] = False
            result['decision'] = 'INVALID_BEFORE'
            result['message'] = f"Before image doesn't show a valid civic issue (detected: {before_class['original_class']})"
            result['confidence'] = before_class['confidence']
            print(f"✗ Invalid before image")
            return result
        
        print(f"✓ Before image shows civic issue: {before_issue}")
        
        # Rule 3: Check if after image shows resolution
        after_issue = after_class['class']
        
        # Work is completed if:
        # - After image is classified as "invalid" (normal/fixed state) with good confidence, AND
        # - The original issue is no longer present (low probability)
        
        # Get confidence for the before issue in the after image
        after_probabilities = after_class.get('all_probabilities', {})
        before_issue_in_after = 0.0
        for class_name, prob in after_probabilities.items():
            if self._normalize_class_name(class_name) == before_issue:
                before_issue_in_after = prob
                break
        
        print(f"  Issue '{before_issue}' probability in after image: {before_issue_in_after:.1%}")
        
        # CRITICAL: Multiple override checks to handle model misclassification
        # Check 1: If "Invalid_data" class has reasonable probability, likely clean
        invalid_prob = after_probabilities.get('Invalid_data', 0.0)
        if invalid_prob == 0.0:
            invalid_prob = after_probabilities.get('invalid_data', 0.0)
        
        print(f"  'Invalid_data' probability in after image: {invalid_prob:.1%}")
        
        # Check 2: Surface quality heuristic
        if after_issue in CIVIC_ISSUES and after_class['confidence'] > 0.70:
            # Model says issue is present with high confidence
            # Apply multiple override conditions (ANY can trigger override)
            
            override_triggered = False
            override_reason = ""
            
            # Condition 1: Surface quality looks clean (LOWERED threshold from 0.70 to 0.60)
            if after_quality['is_likely_clean'] and after_quality['quality_score'] > 0.60:
                override_triggered = True
                override_reason = f"surface quality analysis (score: {after_quality['quality_score']:.2f})"
            
            # Condition 2: Invalid_data class has significant probability (>15%)
            elif invalid_prob > 0.15:
                override_triggered = True
                override_reason = f"'Invalid_data' probability is {invalid_prob:.1%}"
            
            # Condition 3: Very high pothole confidence but low edge intensity suggests false positive
            elif after_issue == 'pothole' and after_quality['edge_intensity'] < 15.0:
                override_triggered = True
                override_reason = f"low edge intensity ({after_quality['edge_intensity']:.1f}) suggests smooth surface"
            
            # Condition 4: Brightness uniformity suggests clean surface
            elif after_quality['brightness_std'] < 25.0:
                override_triggered = True
                override_reason = f"high brightness uniformity (std: {after_quality['brightness_std']:.1f})"
            
            if override_triggered:
                print(f"  ⚠ Model override triggered: {override_reason}")
                result['verified'] = True
                result['decision'] = 'VERIFIED_OVERRIDE'
                result['message'] = f"Work completed successfully! Surface analysis indicates clean area ({override_reason})"
                result['confidence'] = location_similarity * 0.85
                print(f"✓ Verified by override: {override_reason}")
                return result
            else:
                print(f"  No override conditions met (quality: {after_quality['quality_score']:.2f}, invalid_prob: {invalid_prob:.1%}, edge: {after_quality['edge_intensity']:.1f})")
        
        # Check if issue is resolved
        if after_issue in RESOLVED_CATEGORIES and after_class['confidence'] > 0.50:
            # After image shows normal/invalid state with good confidence
            # AND issue should have low probability
            if before_issue_in_after < 0.30:
                result['verified'] = True
                result['decision'] = 'VERIFIED'
                result['message'] = f"Work completed successfully! Location matches and issue appears resolved (before: {before_issue}, after: normal area with {after_class['confidence']:.1%} confidence)"
                result['confidence'] = min(location_similarity, after_class['confidence'])
                print(f"✓ Issue resolved - area now appears normal")
            else:
                # After shows "invalid" but issue still has significant probability
                result['verified'] = False
                result['decision'] = 'NOT_RESOLVED'
                result['message'] = f"Work NOT completed. {before_issue.capitalize()} still detected in after image ({before_issue_in_after:.1%} probability)"
                result['confidence'] = before_issue_in_after
                print(f"✗ Issue still detected despite 'invalid' classification")
            
        elif after_issue == before_issue and after_class['confidence'] > 0.50:
            # Same issue still clearly present with good confidence
            result['verified'] = False
            result['decision'] = 'NOT_RESOLVED'
            result['message'] = f"Work NOT completed. {before_issue.capitalize()} still clearly present in after image ({after_class['confidence']:.1%} confidence)"
            result['confidence'] = after_class['confidence']
            print(f"✗ Issue still present with high confidence")
            
        elif before_issue_in_after < 0.25:
            # Issue probability is very low in after image - likely resolved
            result['verified'] = True
            result['decision'] = 'VERIFIED'
            result['message'] = f"Work completed successfully! Issue significantly reduced (before: {before_issue}, after probability: {before_issue_in_after:.1%})"
            result['confidence'] = location_similarity * (1.0 - before_issue_in_after)
            print(f"✓ Issue significantly reduced")
            
        else:
            # Ambiguous result - issue may still be present
            result['verified'] = False
            result['decision'] = 'AMBIGUOUS'
            result['message'] = f"Unable to confirm work completion: Before shows {before_issue}, after shows {after_issue} ({after_class['confidence']:.1%} confidence, issue probability: {before_issue_in_after:.1%})"
            result['confidence'] = 0.5
            print(f"⚠ Ambiguous - issue may still be present")
        
        return result
    
    def generate_report(self, verification_result: Dict[str, Any]) -> str:
        """
        Generate a formatted verification report.
        
        Args:
            verification_result: Result from verify_completion()
            
        Returns:
            Formatted text report
        """
        report = []
        report.append("\n" + "=" * 80)
        report.append("VERIFICATION REPORT".center(80))
        report.append("=" * 80)
        
        # Decision
        decision = verification_result['decision']
        verified = verification_result['verified']
        
        if verified:
            status = "✓ VERIFIED - WORK COMPLETED"
        else:
            status = f"✗ {decision.replace('_', ' ')}"
        
        report.append(f"\nStatus: {status}")
        report.append(f"Confidence: {verification_result['confidence']:.1%}")
        report.append(f"\nMessage: {verification_result['message']}")
        
        # Details
        details = verification_result.get('details', {})
        
        if 'location_similarity' in details:
            report.append("\n" + "─" * 80)
            report.append("Location Verification")
            report.append("─" * 80)
            sim = details['location_similarity']
            report.append(f"  Similarity Score: {sim:.2%}")
            report.append(f"  Threshold: {LOCATION_SIMILARITY_THRESHOLD:.0%}")
            report.append(f"  Status: {'✓ Same location' if sim >= LOCATION_SIMILARITY_THRESHOLD else '✗ Different locations'}")
        
        if 'before_classification' in details and 'after_classification' in details:
            before = details['before_classification']
            after = details['after_classification']
            
            report.append("\n" + "─" * 80)
            report.append("Classification Results")
            report.append("─" * 80)
            report.append(f"  Before Image: {before['original_class']} ({before['confidence']:.1%} confidence)")
            report.append(f"  After Image:  {after['original_class']} ({after['confidence']:.1%} confidence)")
            
            report.append("\n  Before Image Probabilities:")
            for cls, prob in before['all_probabilities'].items():
                bar = "█" * int(prob * 30)
                report.append(f"    {cls:15} {bar} {prob:.1%}")
            
            report.append("\n  After Image Probabilities:")
            for cls, prob in after['all_probabilities'].items():
                bar = "█" * int(prob * 30)
                report.append(f"    {cls:15} {bar} {prob:.1%}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


# ============================================================================
# STANDALONE USAGE
# ============================================================================
def verify_from_files(before_path: str, after_path: str, expected_issue: str = None):
    """
    Verify work completion from image file paths.
    
    Args:
        before_path: Path to before image
        after_path: Path to after image
        expected_issue: Expected issue type (optional)
    """
    # Initialize verifier
    verifier = WorkCompletionVerifier()
    
    # Load images
    print(f"\nLoading images...")
    print(f"  Before: {before_path}")
    print(f"  After:  {after_path}")
    
    with open(before_path, 'rb') as f:
        before_image = f.read()
    
    with open(after_path, 'rb') as f:
        after_image = f.read()
    
    # Verify completion
    result = verifier.verify_completion(before_image, after_image, expected_issue)
    
    # Generate and print report
    report = verifier.generate_report(result)
    print(report)
    
    return result


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EXAMPLE USAGE")
    print("=" * 80)
    print("\nTo verify work completion from Python:")
    print("""
from ml.verify_completion import WorkCompletionVerifier

verifier = WorkCompletionVerifier()

# Load images
with open('before.jpg', 'rb') as f:
    before_img = f.read()
with open('after.jpg', 'rb') as f:
    after_img = f.read()

# Verify
result = verifier.verify_completion(before_img, after_img, expected_issue='pothole')

# Check result
if result['verified']:
    print("Work completed!")
else:
    print(f"Not verified: {result['message']}")
""")
    
    print("\nTo verify from command line:")
    print("""
python verify_completion.py path/to/before.jpg path/to/after.jpg
""")
    
    print("\n" + "=" * 80)
    
    # Check if command-line arguments provided
    if len(sys.argv) >= 3:
        before_path = sys.argv[1]
        after_path = sys.argv[2]
        expected_issue = sys.argv[3] if len(sys.argv) > 3 else None
        
        verify_from_files(before_path, after_path, expected_issue)
