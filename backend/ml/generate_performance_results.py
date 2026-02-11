"""
Generate Performance Results with Confusion Matrix
Creates comprehensive performance metrics and visualizations for the trained model
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_recall_fscore_support
import json
from datetime import datetime

print("="*70)
print("CivicLens Model Performance Evaluation")
print("="*70)

# Load model and data
print("\n[1/5] Loading model and preparing data...")
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Paths
MODEL_PATH = 'models/civic_classifier.keras'
DATASET_PATH = r'D:\civiclens-frontend\Dataset'
OUTPUT_DIR = 'models'
RESULTS_FILE = os.path.join(OUTPUT_DIR, 'performance_results.txt')
CONFUSION_MATRIX_FILE = os.path.join(OUTPUT_DIR, 'confusion_matrix.png')
METRICS_JSON = os.path.join(OUTPUT_DIR, 'performance_metrics.json')

# Create output directory if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load model
print(f"Loading model from: {MODEL_PATH}")
model = load_model(MODEL_PATH)
print(f"✓ Model loaded successfully")

# Load class names
with open('models/class_names.json', 'r') as f:
    class_names_dict = json.load(f)
    class_names = [class_names_dict[str(i)] for i in range(len(class_names_dict))]

print(f"Classes: {class_names}")

# Prepare validation data generator
print("\n[2/5] Loading validation dataset...")
val_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

val_generator = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(224, 224),
    batch_size=32,
    class_mode='sparse',
    shuffle=False,  # Important for evaluation
    seed=42
)

print(f"Validation samples: {val_generator.samples}")
print(f"Classes found: {val_generator.class_indices}")

# Get predictions
print("\n[3/5] Generating predictions...")
predictions = model.predict(val_generator, verbose=1)
y_pred = np.argmax(predictions, axis=1)
y_true = val_generator.classes

print(f"✓ Predictions complete")
print(f"  Total samples evaluated: {len(y_true)}")

# Calculate metrics
print("\n[4/5] Calculating performance metrics...")

# Overall accuracy
accuracy = accuracy_score(y_true, y_pred)

# Per-class metrics
precision, recall, f1, support = precision_recall_fscore_support(
    y_true, y_pred, average=None, labels=range(len(class_names))
)

# Weighted averages
precision_avg, recall_avg, f1_avg, _ = precision_recall_fscore_support(
    y_true, y_pred, average='weighted'
)

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)

# Classification report
report = classification_report(
    y_true, y_pred, 
    target_names=class_names, 
    digits=4
)

print("✓ Metrics calculated")

# Save results to text file
print("\n[5/5] Saving results...")

with open(RESULTS_FILE, 'w') as f:
    f.write("="*70 + "\n")
    f.write("CIVICLENS MODEL PERFORMANCE RESULTS\n")
    f.write("="*70 + "\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Model: {MODEL_PATH}\n")
    f.write(f"Dataset: {DATASET_PATH}\n")
    f.write(f"Total Samples: {len(y_true)}\n")
    f.write("="*70 + "\n\n")
    
    f.write("OVERALL METRICS\n")
    f.write("-"*70 + "\n")
    f.write(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)\n")
    f.write(f"Precision: {precision_avg:.4f} ({precision_avg*100:.2f}%)\n")
    f.write(f"Recall:    {recall_avg:.4f} ({recall_avg*100:.2f}%)\n")
    f.write(f"F1-Score:  {f1_avg:.4f} ({f1_avg*100:.2f}%)\n")
    f.write("\n")
    
    f.write("PER-CLASS METRICS\n")
    f.write("-"*70 + "\n")
    f.write(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}\n")
    f.write("-"*70 + "\n")
    for i, class_name in enumerate(class_names):
        f.write(f"{class_name:<20} {precision[i]:<12.4f} {recall[i]:<12.4f} {f1[i]:<12.4f} {support[i]:<10}\n")
    f.write("-"*70 + "\n\n")
    
    f.write("CLASSIFICATION REPORT\n")
    f.write("-"*70 + "\n")
    f.write(report)
    f.write("\n\n")
    
    f.write("CONFUSION MATRIX\n")
    f.write("-"*70 + "\n")
    f.write(f"{'':>20}")
    for name in class_names:
        f.write(f"{name[:15]:>15}")
    f.write("\n")
    for i, row in enumerate(cm):
        f.write(f"{class_names[i][:20]:>20}")
        for val in row:
            f.write(f"{val:>15}")
        f.write("\n")

print(f"✓ Results saved to: {RESULTS_FILE}")

# Save metrics as JSON
metrics_dict = {
    "timestamp": datetime.now().isoformat(),
    "model_path": MODEL_PATH,
    "dataset_path": DATASET_PATH,
    "total_samples": int(len(y_true)),
    "overall_metrics": {
        "accuracy": float(accuracy),
        "precision": float(precision_avg),
        "recall": float(recall_avg),
        "f1_score": float(f1_avg)
    },
    "per_class_metrics": {
        class_names[i]: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1_score": float(f1[i]),
            "support": int(support[i])
        }
        for i in range(len(class_names))
    },
    "confusion_matrix": cm.tolist()
}

with open(METRICS_JSON, 'w') as f:
    json.dump(metrics_dict, f, indent=2)

print(f"✓ Metrics JSON saved to: {METRICS_JSON}")

# Create confusion matrix visualization
print("\nCreating confusion matrix visualization...")

plt.figure(figsize=(12, 10))

# Plot confusion matrix
ax = plt.subplot(111)
sns.heatmap(
    cm, 
    annot=True, 
    fmt='d', 
    cmap='Blues',
    xticklabels=class_names,
    yticklabels=class_names,
    cbar_kws={'label': 'Count'},
    annot_kws={'size': 12, 'weight': 'bold'}
)

plt.title('Confusion Matrix - CivicLens Model\n', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Predicted Label', fontsize=12, fontweight='bold')
plt.ylabel('True Label', fontsize=12, fontweight='bold')

# Add accuracy text
accuracy_text = f'Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)'
plt.text(
    0.5, -0.15, accuracy_text,
    transform=ax.transAxes,
    ha='center',
    fontsize=14,
    fontweight='bold',
    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
)

# Add metrics table
metrics_text = f'Precision: {precision_avg:.4f} | Recall: {recall_avg:.4f} | F1-Score: {f1_avg:.4f}'
plt.text(
    0.5, -0.20, metrics_text,
    transform=ax.transAxes,
    ha='center',
    fontsize=11,
    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
)

plt.tight_layout()
plt.savefig(CONFUSION_MATRIX_FILE, dpi=300, bbox_inches='tight')
print(f"✓ Confusion matrix saved to: {CONFUSION_MATRIX_FILE}")

# Also create a detailed performance visualization
print("\nCreating detailed performance visualization...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('CivicLens Model - Detailed Performance Metrics', fontsize=18, fontweight='bold', y=0.995)

# 1. Confusion Matrix (normalized)
ax1 = axes[0, 0]
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
sns.heatmap(
    cm_normalized,
    annot=True,
    fmt='.2%',
    cmap='RdYlGn',
    xticklabels=class_names,
    yticklabels=class_names,
    ax=ax1,
    cbar_kws={'label': 'Percentage'}
)
ax1.set_title('Normalized Confusion Matrix (%)', fontsize=14, fontweight='bold', pad=10)
ax1.set_xlabel('Predicted Label', fontweight='bold')
ax1.set_ylabel('True Label', fontweight='bold')

# 2. Per-Class Metrics Bar Chart
ax2 = axes[0, 1]
x = np.arange(len(class_names))
width = 0.25

bars1 = ax2.bar(x - width, precision, width, label='Precision', color='#3498db')
bars2 = ax2.bar(x, recall, width, label='Recall', color='#2ecc71')
bars3 = ax2.bar(x + width, f1, width, label='F1-Score', color='#e74c3c')

ax2.set_xlabel('Class', fontweight='bold')
ax2.set_ylabel('Score', fontweight='bold')
ax2.set_title('Per-Class Performance Metrics', fontsize=14, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(class_names, rotation=45, ha='right')
ax2.legend()
ax2.set_ylim(0, 1.1)
ax2.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=8)

# 3. Class Distribution
ax3 = axes[1, 0]
colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
ax3.bar(class_names, support, color=colors, alpha=0.7, edgecolor='black')
ax3.set_xlabel('Class', fontweight='bold')
ax3.set_ylabel('Number of Samples', fontweight='bold')
ax3.set_title('Class Distribution in Dataset', fontsize=14, fontweight='bold', pad=10)
ax3.tick_params(axis='x', rotation=45)
ax3.grid(axis='y', alpha=0.3)

# Add value labels
for i, (name, val) in enumerate(zip(class_names, support)):
    ax3.text(i, val, f'{val}', ha='center', va='bottom', fontweight='bold')

# 4. Overall Metrics Summary
ax4 = axes[1, 1]
ax4.axis('off')

summary_text = f"""
OVERALL PERFORMANCE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Accuracy:        {accuracy:.4f} ({accuracy*100:.2f}%)
Precision (avg): {precision_avg:.4f} ({precision_avg*100:.2f}%)
Recall (avg):    {recall_avg:.4f} ({recall_avg*100:.2f}%)
F1-Score (avg):  {f1_avg:.4f} ({f1_avg*100:.2f}%)

Total Samples:   {len(y_true):,}
Classes:         {len(class_names)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODEL INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Architecture:    MobileNetV2
Parameters:      2,428,100
Model Size:      11.6 MB
Input Shape:     (224, 224, 3)
Output Classes:  4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

ax4.text(
    0.1, 0.95, summary_text,
    transform=ax4.transAxes,
    fontsize=11,
    verticalalignment='top',
    fontfamily='monospace',
    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
)

plt.tight_layout()
detailed_plot_file = os.path.join(OUTPUT_DIR, 'detailed_performance_metrics.png')
plt.savefig(detailed_plot_file, dpi=300, bbox_inches='tight')
print(f"✓ Detailed performance visualization saved to: {detailed_plot_file}")

# Print summary to console
print("\n" + "="*70)
print("PERFORMANCE SUMMARY")
print("="*70)
print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Precision: {precision_avg:.4f} ({precision_avg*100:.2f}%)")
print(f"Recall:    {recall_avg:.4f} ({recall_avg*100:.2f}%)")
print(f"F1-Score:  {f1_avg:.4f} ({f1_avg*100:.2f}%)")
print("="*70)
print("\nPer-Class Metrics:")
print("-"*70)
print(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12}")
print("-"*70)
for i, class_name in enumerate(class_names):
    print(f"{class_name:<20} {precision[i]:<12.4f} {recall[i]:<12.4f} {f1[i]:<12.4f}")
print("="*70)

print("\n✓ All performance results generated successfully!")
print(f"\nFiles created:")
print(f"  1. {RESULTS_FILE}")
print(f"  2. {CONFUSION_MATRIX_FILE}")
print(f"  3. {detailed_plot_file}")
print(f"  4. {METRICS_JSON}")
