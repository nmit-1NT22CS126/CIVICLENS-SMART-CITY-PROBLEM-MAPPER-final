"""
CivicLens AI Pipeline - MobileNetV2 Training Script (FIXED)
============================================================
Fixes applied:
1. SparseCategoricalCrossentropy with from_logits=False (softmax output)
2. Sparse label mode (integer labels 0, 1, 2, 3)
3. MobileNetV2 preprocess_input (NOT rescale=1./255)
4. Capped class weights (max 3.0)
5. Proper output layer: Dense(4, activation='softmax')

Classes: Garbage, Invalid_data, Potholes, water logging
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

print("=" * 70)
print("CivicLens MobileNetV2 Training Pipeline (FIXED)")
print("=" * 70)

# ============================================================================
# CONFIGURATION
# ============================================================================
DATASET_PATH = r"D:\civiclens-frontend\Dataset"
MODEL_SAVE_PATH = r"D:\civiclens-frontend\backend\ml\models"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32  # Larger batch for MobileNetV2 (lighter model)
EPOCHS = 20
LEARNING_RATE = 1e-3
FINE_TUNE_EPOCHS = 10
FINE_TUNE_LR = 1e-5

print(f"\nConfiguration:")
print(f"  - Image Size: {IMG_SIZE}")
print(f"  - Batch Size: {BATCH_SIZE}")
print(f"  - Initial Epochs: {EPOCHS}")
print(f"  - Fine-tune Epochs: {FINE_TUNE_EPOCHS}")
print(f"  - Learning Rate: {LEARNING_RATE}")

# ============================================================================
# IMPORTS
# ============================================================================
print("\n[1/8] Importing TensorFlow and dependencies...")

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.utils.class_weight import compute_class_weight

print(f"TensorFlow version: {tf.__version__}")
print(f"GPU Available: {tf.config.list_physical_devices('GPU')}")

# ============================================================================
# DATASET ANALYSIS
# ============================================================================
print("\n[2/8] Analyzing dataset structure...")

class_counts = {}
total_images = 0

for folder in os.listdir(DATASET_PATH):
    folder_path = os.path.join(DATASET_PATH, folder)
    if os.path.isdir(folder_path):
        count = len([f for f in os.listdir(folder_path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))])
        class_counts[folder] = count
        total_images += count
        print(f"  {folder}: {count} images")

print(f"\nTotal images: {total_images}")

# ============================================================================
# DATA GENERATORS - FIXED PREPROCESSING
# ============================================================================
print("\n[3/8] Creating data generators with FIXED preprocessing...")

# CRITICAL FIX: Use MobileNetV2's preprocess_input instead of rescale=1./255
# MobileNetV2 expects inputs normalized to [-1, 1], not [0, 1]

train_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input,  # MobileNetV2 preprocessing [-1, 1]
    rotation_range=20,
    width_shift_range=0.15,
    height_shift_range=0.15,
    shear_range=0.15,
    zoom_range=0.15,
    horizontal_flip=True,
    brightness_range=[0.8, 1.2],
    fill_mode='nearest',
    validation_split=0.2
)

val_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input,  # Same preprocessing for validation
    validation_split=0.2
)

# CRITICAL FIX: Use sparse labels (integers) instead of categorical (one-hot)
train_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='sparse',  # Integer labels: 0, 1, 2, 3
    subset='training',
    shuffle=True,
    seed=42
)

val_generator = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='sparse',  # Integer labels
    subset='validation',
    shuffle=False,
    seed=42
)

# Get class info
class_indices = train_generator.class_indices
num_classes = len(class_indices)

print(f"\nClass indices: {class_indices}")
print(f"Number of classes: {num_classes}")
print(f"Training samples: {train_generator.samples}")
print(f"Validation samples: {val_generator.samples}")

# Save class names mapping
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
class_names_map = {v: k for k, v in class_indices.items()}
with open(os.path.join(MODEL_SAVE_PATH, 'class_names.json'), 'w') as f:
    json.dump(class_names_map, f, indent=2)
print(f"Class names saved to {MODEL_SAVE_PATH}/class_names.json")

# ============================================================================
# COMPUTE CLASS WEIGHTS (Capped to prevent exploding loss)
# ============================================================================
print("\n[4/8] Computing class weights...")

class_weight_values = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(list(class_indices.values())),
    y=train_generator.classes
)

# CAP class weights to prevent extreme values
MAX_WEIGHT = 3.0
class_weight_values = np.clip(class_weight_values, 0.5, MAX_WEIGHT)
class_weights = dict(enumerate(class_weight_values))
print(f"Class weights (capped at {MAX_WEIGHT}): {class_weights}")

# ============================================================================
# BUILD MOBILENETV2 MODEL
# ============================================================================
print("\n[5/8] Building MobileNetV2 model...")

def build_model(num_classes):
    """Build MobileNetV2 with custom classification head."""
    
    # Load pretrained MobileNetV2
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3),
        pooling=None
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Build model
    inputs = keras.Input(shape=(224, 224, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    
    # CRITICAL: 4 classes with softmax activation
    outputs = layers.Dense(num_classes, activation='softmax', name='predictions')(x)
    
    model = Model(inputs, outputs, name='CivicLens_MobileNetV2')
    
    return model, base_model

model, base_model = build_model(num_classes)
model.summary()

# ============================================================================
# COMPILE MODEL - FIXED LOSS FUNCTION
# ============================================================================
print("\n[6/8] Compiling model with FIXED loss function...")

# CRITICAL FIX: SparseCategoricalCrossentropy for integer labels
# from_logits=False because we use softmax activation
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=False),
    metrics=['accuracy']
)

print(f"✓ Loss: SparseCategoricalCrossentropy(from_logits=False)")
print(f"✓ Labels: Sparse (integers 0, 1, 2, 3)")
print(f"✓ Output: Dense({num_classes}, activation='softmax')")

# ============================================================================
# CALLBACKS
# ============================================================================
callbacks = [
    ModelCheckpoint(
        os.path.join(MODEL_SAVE_PATH, 'best_mobilenet.keras'),
        monitor='val_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    ),
    EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
]

# ============================================================================
# INITIAL TRAINING (Frozen base)
# ============================================================================
print("\n[7/8] Training (frozen base)...")
print("=" * 50)
print("Expected: Loss should start between 1.3 - 1.8")
print("=" * 50)

history = model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=val_generator,
    class_weight=class_weights,
    callbacks=callbacks,
    verbose=1
)

# ============================================================================
# FINE-TUNING (Unfreeze top layers)
# ============================================================================
print("\n[8/8] Fine-tuning (unfreezing top 30 layers)...")
print("=" * 50)

# Unfreeze top 30 layers of MobileNetV2
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

trainable_layers = sum(1 for layer in base_model.layers if layer.trainable)
print(f"Trainable base layers: {trainable_layers}")

# Recompile with lower learning rate
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=False),
    metrics=['accuracy']
)

# Continue training
history_fine = model.fit(
    train_generator,
    epochs=FINE_TUNE_EPOCHS,
    validation_data=val_generator,
    class_weight=class_weights,
    callbacks=callbacks,
    verbose=1
)

# ============================================================================
# SAVE MODELS
# ============================================================================
print("\nSaving models...")

model.save(os.path.join(MODEL_SAVE_PATH, 'civic_classifier.keras'))
model.save(os.path.join(MODEL_SAVE_PATH, 'civic_classifier.h5'))
model.save(os.path.join(MODEL_SAVE_PATH, 'final_pipeline.keras'))
model.save(os.path.join(MODEL_SAVE_PATH, 'final_pipeline.h5'))

print(f"✓ Models saved to {MODEL_SAVE_PATH}")

# ============================================================================
# EVALUATION
# ============================================================================
print("\n" + "=" * 70)
print("MODEL EVALUATION")
print("=" * 70)

# Get predictions
val_generator.reset()
predictions = model.predict(val_generator, verbose=1)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = val_generator.classes

# Classification Report
print("\nClassification Report:")
print("-" * 50)
target_names = [class_names_map[i] for i in range(num_classes)]
report = classification_report(true_classes, predicted_classes, target_names=target_names)
print(report)

# F1 Scores
f1_macro = f1_score(true_classes, predicted_classes, average='macro')
f1_weighted = f1_score(true_classes, predicted_classes, average='weighted')
print(f"\nF1 Score (Macro): {f1_macro:.4f}")
print(f"F1 Score (Weighted): {f1_weighted:.4f}")

# Confusion Matrix
print("\nConfusion Matrix:")
cm = confusion_matrix(true_classes, predicted_classes)
print(cm)

# Save metrics
final_val_acc = history_fine.history['val_accuracy'][-1] if history_fine else history.history['val_accuracy'][-1]
metrics = {
    'f1_macro': float(f1_macro),
    'f1_weighted': float(f1_weighted),
    'val_accuracy': float(final_val_acc),
    'class_names': target_names,
    'model_type': 'MobileNetV2',
    'training_samples': train_generator.samples,
    'validation_samples': val_generator.samples
}

with open(os.path.join(MODEL_SAVE_PATH, 'metrics.json'), 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"\n✓ Metrics saved to {MODEL_SAVE_PATH}/metrics.json")
print("\n" + "=" * 70)
print("TRAINING COMPLETE!")
print(f"Final Validation Accuracy: {final_val_acc:.2%}")
print(f"F1 Score (Weighted): {f1_weighted:.4f}")
print("=" * 70)
