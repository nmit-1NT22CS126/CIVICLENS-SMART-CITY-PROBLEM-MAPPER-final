"""
CivicLens Model Performance Viewer
===================================
Displays comprehensive performance metrics in terminal with ASCII visualization
No training required - just loads and evaluates the existing model
"""

import os
import sys
import json
import numpy as np
from datetime import datetime

print("=" * 80)
print("CIVICLENS MODEL PERFORMANCE VIEWER".center(80))
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = 'models/civic_classifier.keras'
DATASET_PATH = r'D:\civiclens-frontend\Dataset'
CLASS_NAMES_PATH = 'models/class_names.json'

# ============================================================================
# LOAD DEPENDENCIES
# ============================================================================
print("\n[1/5] Loading dependencies...")
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from sklearn.metrics import (
    confusion_matrix, 
    classification_report, 
    accuracy_score,
    precision_recall_fscore_support
)

print("✓ Dependencies loaded")

# ============================================================================
# LOAD MODEL
# ============================================================================
print("\n[2/5] Loading trained model...")
print(f"Model path: {MODEL_PATH}")

try:
    model = load_model(MODEL_PATH)
    print("✓ Model loaded successfully")
    print(f"  - Model name: {model.name}")
    print(f"  - Total parameters: {model.count_params():,}")
    print(f"  - Input shape: {model.input_shape}")
    print(f"  - Output shape: {model.output_shape}")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    sys.exit(1)

# Load class names
try:
    with open(CLASS_NAMES_PATH, 'r') as f:
        class_names_dict = json.load(f)
        class_names = [class_names_dict[str(i)] for i in range(len(class_names_dict))]
    print(f"✓ Class names: {class_names}")
except Exception as e:
    print(f"⚠ Warning: Could not load class names: {e}")
    class_names = ['Class_0', 'Class_1', 'Class_2', 'Class_3']

# ============================================================================
# LOAD DATASET
# ============================================================================
print("\n[3/5] Loading dataset for evaluation...")
print(f"Dataset path: {DATASET_PATH}")

val_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

val_generator = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(224, 224),
    batch_size=32,
    class_mode='sparse',
    shuffle=False,
    seed=42
)

print(f"✓ Dataset loaded")
print(f"  - Total samples: {val_generator.samples}")
print(f"  - Class distribution: {dict(val_generator.class_indices)}")

# ============================================================================
# GENERATE PREDICTIONS
# ============================================================================
print("\n[4/5] Generating predictions...")
print("This may take 1-2 minutes for full dataset evaluation...")

predictions = model.predict(val_generator, verbose=0)
y_pred = np.argmax(predictions, axis=1)
y_true = val_generator.classes

print(f"✓ Predictions complete")
print(f"  - Samples evaluated: {len(y_true)}")

# ============================================================================
# CALCULATE METRICS
# ============================================================================
print("\n[5/5] Calculating performance metrics...")

# Overall accuracy
accuracy = accuracy_score(y_true, y_pred)

# Per-class metrics
precision, recall, f1, support = precision_recall_fscore_support(
    y_true, y_pred, 
    average=None, 
    labels=range(len(class_names))
)

# Weighted averages
precision_avg, recall_avg, f1_avg, _ = precision_recall_fscore_support(
    y_true, y_pred, 
    average='weighted'
)

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)

print("✓ Metrics calculated")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("PERFORMANCE RESULTS".center(80))
print("=" * 80)

# Header info
print(f"\nModel: {MODEL_PATH}")
print(f"Evaluated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total Samples: {len(y_true):,}")
print(f"Architecture: MobileNetV2")

# Overall metrics
print("\n" + "─" * 80)
print("OVERALL METRICS")
print("─" * 80)
print(f"{'Metric':<20} {'Score':<15} {'Percentage':<15}")
print("─" * 80)
print(f"{'Accuracy':<20} {accuracy:<15.4f} {accuracy*100:<15.2f}%")
print(f"{'Precision (Avg)':<20} {precision_avg:<15.4f} {precision_avg*100:<15.2f}%")
print(f"{'Recall (Avg)':<20} {recall_avg:<15.4f} {recall_avg*100:<15.2f}%")
print(f"{'F1-Score (Avg)':<20} {f1_avg:<15.4f} {f1_avg*100:<15.2f}%")

# Per-class metrics
print("\n" + "─" * 80)
print("PER-CLASS PERFORMANCE")
print("─" * 80)
print(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
print("─" * 80)

for i, class_name in enumerate(class_names):
    print(f"{class_name:<20} {precision[i]:<12.4f} {recall[i]:<12.4f} {f1[i]:<12.4f} {support[i]:<10}")

# Confusion Matrix (ASCII visualization)
print("\n" + "─" * 80)
print("CONFUSION MATRIX")
print("─" * 80)
print("Rows: True Labels | Columns: Predicted Labels\n")

# Header
max_len = max(len(name) for name in class_names)
col_width = max(8, max_len + 2)

print(" " * (max_len + 2), end="")
for name in class_names:
    print(f"{name[:8]:^{col_width}}", end="")
print()
print("─" * (max_len + 2 + col_width * len(class_names)))

# Matrix rows
for i, true_class in enumerate(class_names):
    print(f"{true_class:<{max_len + 2}}", end="")
    for j in range(len(class_names)):
        count = cm[i][j]
        if i == j:
            # Diagonal (correct predictions) - highlighted
            print(f"[{count:^6}]  ", end="")
        else:
            # Off-diagonal (errors)
            print(f" {count:^6}   ", end="")
    print()

# Accuracy per class (diagonal / total per class)
print("\n" + "─" * 80)
print("ACCURACY BREAKDOWN")
print("─" * 80)

correct = np.diag(cm)
total = cm.sum(axis=1)
class_accuracy = correct / total

print(f"{'Class':<20} {'Correct':<12} {'Total':<12} {'Accuracy':<12}")
print("─" * 80)
for i, class_name in enumerate(class_names):
    print(f"{class_name:<20} {correct[i]:<12} {total[i]:<12} {class_accuracy[i]*100:<12.2f}%")

# Visual performance bars
print("\n" + "─" * 80)
print("VISUAL PERFORMANCE (F1-Score)")
print("─" * 80)

for i, class_name in enumerate(class_names):
    bar_length = int(f1[i] * 50)  # Scale to 50 characters
    bar = "█" * bar_length + "░" * (50 - bar_length)
    print(f"{class_name:<20} {bar} {f1[i]*100:>6.2f}%")

# Overall summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_correct = np.sum(np.diag(cm))
total_samples = np.sum(cm)
print(f"✓ Correctly Classified: {total_correct:,} / {total_samples:,} ({accuracy*100:.2f}%)")
print(f"✗ Misclassified: {total_samples - total_correct:,} ({(1-accuracy)*100:.2f}%)")
print(f"\nBest Performing Class: {class_names[np.argmax(f1)]} (F1: {np.max(f1)*100:.2f}%)")
print(f"Worst Performing Class: {class_names[np.argmin(f1)]} (F1: {np.min(f1)*100:.2f}%)")

# Grade assignment
if accuracy >= 0.95:
    grade = "A+ (Excellent)"
elif accuracy >= 0.90:
    grade = "A (Very Good)"
elif accuracy >= 0.85:
    grade = "B (Good)"
elif accuracy >= 0.80:
    grade = "C (Acceptable)"
else:
    grade = "D (Needs Improvement)"

print(f"\nOverall Grade: {grade}")

print("\n" + "=" * 80)
print("✓ Performance evaluation complete!".center(80))
print("=" * 80)

# Classification Report (sklearn format)
print("\n" + "─" * 80)
print("DETAILED CLASSIFICATION REPORT")
print("─" * 80)
report = classification_report(
    y_true, y_pred,
    target_names=class_names,
    digits=4
)
print(report)
print("─" * 80)
