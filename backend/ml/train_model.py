"""
CivicLens Model Training Script
Trains a 4-class classifier: Garbage, Invalid_data, Potholes, water logging
"""

import os
import sys
import json
import numpy as np

print("=" * 60)
print("CivicLens Model Training - Version 2")
print("=" * 60)

# Configuration
DATASET_PATH = r"D:\civiclens-frontend\Dataset"
MODEL_SAVE_PATH = r"D:\civiclens-frontend\backend\ml\models"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

print("\n[1/7] Importing TensorFlow...")
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator

print(f"TensorFlow version: {tf.__version__}")
print(f"GPU Available: {tf.config.list_physical_devices('GPU')}")

# Check dataset
print("\n[2/7] Checking dataset structure...")
for folder in os.listdir(DATASET_PATH):
    folder_path = os.path.join(DATASET_PATH, folder)
    if os.path.isdir(folder_path):
        count = len([f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        print(f"  {folder}: {count} images")

# Data generators
print("\n[3/7] Creating data generators...")
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)

val_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

class_names = list(train_generator.class_indices.keys())
num_classes = len(class_names)
print(f"\nClasses: {class_names}")
print(f"Training samples: {train_generator.samples}")
print(f"Validation samples: {val_generator.samples}")

# Build model
print("\n[4/7] Building MobileNetV2 model...")
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)
base_model.trainable = False

model = keras.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    layers.Dense(256, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    layers.Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(f"Model built with {num_classes} output classes")

# Callbacks
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=3,
        min_lr=1e-6
    )
]

# Phase 1: Train top layers
print("\n[5/7] Phase 1: Training top layers (10 epochs)...")
history1 = model.fit(
    train_generator,
    epochs=10,
    validation_data=val_generator,
    callbacks=callbacks,
    verbose=1
)

# Phase 2: Fine-tuning
print("\n[6/7] Phase 2: Fine-tuning (10 epochs)...")
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

history2 = model.fit(
    train_generator,
    epochs=10,
    validation_data=val_generator,
    callbacks=callbacks,
    verbose=1
)

# Evaluate
print("\n[7/7] Evaluating and saving model...")
val_generator.reset()
val_loss, val_acc = model.evaluate(val_generator, verbose=0)
print(f"\nFinal Validation Accuracy: {val_acc*100:.2f}%")
print(f"Final Validation Loss: {val_loss:.4f}")

# Save model
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
model_file = os.path.join(MODEL_SAVE_PATH, 'civic_classifier.keras')
model.save(model_file)
print(f"\nModel saved to: {model_file}")

# Save class names
class_mapping = {str(v): k for k, v in train_generator.class_indices.items()}
class_names_file = os.path.join(MODEL_SAVE_PATH, 'class_names.json')
with open(class_names_file, 'w') as f:
    json.dump(class_mapping, f, indent=2)
print(f"Class names saved to: {class_names_file}")

print("\n" + "=" * 60)
print("CLASS MAPPING:")
for idx, name in class_mapping.items():
    print(f"  {idx}: {name}")
print("=" * 60)
print("\n✅ Training complete!")
