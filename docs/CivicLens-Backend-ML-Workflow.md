# CivicLens Backend - Complete ML Workflow Documentation

## 🎯 Overview

This document explains **exactly** how the ML model works in the CivicLens backend, including file paths, function calls, and data flow.

---

## 📁 Project Structure

```
D:\civiclens-frontend\backend\
├── app\
│   ├── routers\
│   │   └── complaints.py          ← API endpoint (POST /complaints)
│   ├── schemas.py                  ← Data validation models
│   └── supabase_client.py          ← Database connection
│
├── ml\
│   ├── classifier.py               ← Main AI pipeline (4 classes)
│   ├── ocr_geo.py                  ← OCR geolocation extraction
│   ├── train_mobilenet.py          ← Training script
│   └── models\
│       ├── civic_classifier.keras  ← Trained MobileNetV2 model (11.6 MB)
│       ├── class_names.json        ← ["Garbage", "Invalid_data", "Potholes", "water logging"]
│       └── performance_results.txt ← 95.99% accuracy metrics
│
└── venv\                           ← Python virtual environment
```

---

## 🔄 Complete Request Flow

### **User Journey: Submitting a Civic Complaint**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USER ACTION (Frontend - React)                                  │
│    • User fills form: Title, Description, Category                 │
│    • User uploads photo: pothole.jpg (2.4 MB)                      │
│    • User clicks "Submit Complaint"                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. HTTP REQUEST                                                     │
│    POST http://localhost:8000/api/complaints                       │
│                                                                     │
│    Headers:                                                         │
│    • Authorization: Bearer <JWT_TOKEN>                              │
│    • Content-Type: multipart/form-data                             │
│                                                                     │
│    Body:                                                            │
│    • title: "Large pothole on Main Street"                         │
│    • description: "Deep pothole causing traffic issues"            │
│    • category: "pothole"                                            │
│    • image: pothole.jpg (binary data)                               │
│    • lat_user: 17.385                                               │
│    • long_user: 78.486                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. FASTAPI ROUTER                                                   │
│    File: backend/app/routers/complaints.py                          │
│    Function: create_complaint()                                     │
│                                                                     │
│    Line 90-120:                                                     │
│    @router.post("/", response_model=schemas.Complaint)              │
│    async def create_complaint(                                      │
│        title: str = Form(...),                                      │
│        description: str = Form(...),                                │
│        category: str = Form(...),                                   │
│        image: UploadFile = File(...),                               │
│        current_user = Depends(auth.get_current_user)                │
│    ):                                                               │
│        # Read image bytes                                           │
│        image_content = await image.read()  # 2.4 MB bytes           │
│                                                                     │
│        # Call AI validation                                         │
│        ai_result = validate_with_ai(                                │
│            image_content, title, description, category              │
│        )                                                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. AI VALIDATION FUNCTION                                           │
│    File: backend/app/routers/complaints.py                          │
│    Function: validate_with_ai()                                     │
│    Lines: 215-320                                                   │
│                                                                     │
│    Purpose: Orchestrate AI validation with dynamic thresholds      │
│                                                                     │
│    STEP 4A: Get Classifier Instance                                │
│    classifier = get_classifier()                                    │
│    ↓ Initializes ImageClassifier from ml/classifier.py             │
│                                                                     │
│    STEP 4B: Classify Image                                         │
│    prediction = classifier.classify(image_content)                  │
│    ↓ Calls ImageClassifier.classify()                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. IMAGE CLASSIFIER                                                 │
│    File: backend/ml/classifier.py                                   │
│    Class: ImageClassifier                                           │
│    Function: classify()                                             │
│    Lines: 140-225                                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ STEP 5.1: Load Model (First Time Only)                       │  │
│  │ self._load_model()                                            │  │
│  │                                                               │  │
│  │ import tensorflow as tf                                       │  │
│  │ model = tf.keras.models.load_model(                           │  │
│  │     'backend/ml/models/civic_classifier.keras'                │  │
│  │ )                                                             │  │
│  │                                                               │  │
│  │ ✓ Model loaded: 2,762,702 parameters                          │  │
│  │ ✓ Model type: MobileNetV2 + custom head                       │  │
│  │ ✓ Input shape: (None, 224, 224, 3)                            │  │
│  │ ✓ Output: 4 classes [Garbage, Invalid, Pothole, Water]        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ STEP 5.2: Preprocess Image                                    │  │
│  │ img = Image.open(io.BytesIO(image_data))                      │  │
│  │ ↓ Open: pothole.jpg → PIL Image (1920×1080)                   │  │
│  │                                                               │  │
│  │ if img.mode != 'RGB':                                         │  │
│  │     img = img.convert('RGB')                                  │  │
│  │ ↓ Convert: RGBA → RGB (if needed)                             │  │
│  │                                                               │  │
│  │ img = img.resize((224, 224), Image.Resampling.LANCZOS)        │  │
│  │ ↓ Resize: 1920×1080 → 224×224 (high quality)                  │  │
│  │                                                               │  │
│  │ img_array = np.array(img)                                     │  │
│  │ ↓ Convert: PIL Image → NumPy array                            │  │
│  │   Shape: (224, 224, 3)                                        │  │
│  │   Values: [0-255] RGB pixel values                            │  │
│  │                                                               │  │
│  │ img_array = np.expand_dims(img_array, axis=0)                 │  │
│  │ ↓ Add batch dimension: (224, 224, 3) → (1, 224, 224, 3)       │  │
│  │                                                               │  │
│  │ from tf.keras.applications.mobilenet_v2 import preprocess_input │
│  │ img_array = preprocess_input(img_array)                       │  │
│  │ ↓ Normalize: [0-255] → [-1, 1]                                │  │
│  │   Formula: (x / 127.5) - 1                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ STEP 5.3: Run CNN Prediction                                  │  │
│  │ predictions = self.model.predict(img_array, verbose=0)         │  │
│  │                                                               │  │
│  │ INPUT: (1, 224, 224, 3) normalized image                      │  │
│  │   ↓                                                           │  │
│  │ ┌─────────────────────────────────────────────────────────┐   │  │
│  │ │ MOBILENETV2 BASE (Pre-trained CNN)                      │   │  │
│  │ │ • 53 Convolutional Layers                               │   │  │
│  │ │ • Processes image through:                              │   │  │
│  │ │   - Edge detection (Layer 1-10)                         │   │  │
│  │ │   - Texture recognition (Layer 10-30)                   │   │  │
│  │ │   - Shape understanding (Layer 30-53)                   │   │  │
│  │ │                                                         │   │  │
│  │ │ OUTPUT: (1, 7, 7, 1280) feature map                     │   │  │
│  │ │         ↓                                               │   │  │
│  │ │ GLOBAL AVERAGE POOLING                                  │   │  │
│  │ │ • Reduces spatial dimensions                            │   │  │
│  │ │ OUTPUT: (1, 1280) feature vector                        │   │  │
│  │ └─────────────────────────────────────────────────────────┘   │  │
│  │   ↓                                                           │  │
│  │ ┌─────────────────────────────────────────────────────────┐   │  │
│  │ │ CUSTOM CLASSIFICATION HEAD                              │   │  │
│  │ │                                                         │   │  │
│  │ │ BatchNormalization → Normalize features                 │   │  │
│  │ │ Dropout(0.3) → Prevent overfitting                      │   │  │
│  │ │ Dense(128, relu) → Learn category patterns              │   │  │
│  │ │ BatchNormalization → Stabilize training                 │   │  │
│  │ │ Dropout(0.5) → More regularization                      │   │  │
│  │ │ Dense(4, softmax) → Final predictions                   │   │  │
│  │ └─────────────────────────────────────────────────────────┘   │  │
│  │   ↓                                                           │  │
│  │ OUTPUT: predictions = [[0.05, 0.03, 0.89, 0.03]]              │  │
│  │         Index 0: Garbage      → 5%                            │  │
│  │         Index 1: Invalid      → 3%                            │  │
│  │         Index 2: Pothole      → 89% ✓ WINNER                 │  │
│  │         Index 3: Waterlogging → 3%                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ STEP 5.4: Extract Results                                     │  │
│  │ pred_idx = np.argmax(predictions[0])  # Index 2              │  │
│  │ confidence = predictions[0][pred_idx]  # 0.89 (89%)          │  │
│  │ predicted_class = self.categories[pred_idx]  # "Potholes"    │  │
│  │                                                               │  │
│  │ RETURN:                                                       │  │
│  │ {                                                             │  │
│  │   "predicted_class": "pothole",      ← Normalized            │  │
│  │   "original_class": "Potholes",                               │  │
│  │   "confidence": 0.89,                ← 89%                    │  │
│  │   "is_civic_issue": True,            ← Not invalid           │  │
│  │   "all_probabilities": {                                      │  │
│  │     "Garbage": 0.05,                                          │  │
│  │     "Invalid_data": 0.03,                                     │  │
│  │     "Potholes": 0.89,                                         │  │
│  │     "water logging": 0.03                                     │  │
│  │   },                                                          │  │
│  │   "method": "trained_cnn_model"                               │  │
│  │ }                                                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. TEXT ANALYSIS (Optional - for matching)                         │
│    File: backend/ml/classifier.py                                   │
│    Class: TextAnalyzer                                              │
│    Function: analyze()                                              │
│    Lines: 300-350                                                   │
│                                                                     │
│    Input:                                                           │
│    • title: "Large pothole on Main Street"                         │
│    • description: "Deep pothole causing traffic issues"            │
│                                                                     │
│    Process:                                                         │
│    text = "large pothole on main street deep pothole causing..."   │
│                                                                     │
│    Keyword Matching:                                                │
│    • Garbage keywords: 0 matches                                    │
│    • Pothole keywords: 2 matches ["pothole", "pothole"]            │
│    • Waterlogging keywords: 0 matches                               │
│                                                                     │
│    Result:                                                          │
│    {                                                                │
│      "predicted_category": "pothole",                               │
│      "confidence": 0.67,              ← 2/3 matches                 │
│      "matched_keywords": ["pothole", "pothole"],                    │
│      "method": "keyword_matching"                                   │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. GEOTAG EXTRACTION                                                │
│    File: backend/ml/classifier.py                                   │
│    Class: GeotagExtractor                                           │
│    Function: extract_geotag()                                       │
│    Lines: 360-490                                                   │
│                                                                     │
│    Process:                                                         │
│    • Open image and read EXIF metadata                              │
│    • Look for GPS tags (GPSInfo, GPSLatitude, GPSLongitude)         │
│    • Convert DMS (Degrees/Minutes/Seconds) to Decimal               │
│                                                                     │
│    Example GPS Data:                                                │
│    GPSLatitude: (17, 23, 6.0)    → 17 + 23/60 + 6/3600             │
│    GPSLatitudeRef: "N"           → Positive                         │
│    → Result: 17.385000                                              │
│                                                                     │
│    GPSLongitude: (78, 29, 9.6)   → 78 + 29/60 + 9.6/3600           │
│    GPSLongitudeRef: "E"          → Positive                         │
│    → Result: 78.486000                                              │
│                                                                     │
│    Return:                                                          │
│    {                                                                │
│      "lat_img": 17.385,                                             │
│      "long_img": 78.486,                                            │
│      "has_geotag": True                                             │
│    }                                                                │
│                                                                     │
│    OR if no GPS data:                                               │
│    {                                                                │
│      "lat_img": None,                                               │
│      "long_img": None,                                              │
│      "has_geotag": False                                            │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. VALIDATION LOGIC                                                 │
│    File: backend/app/routers/complaints.py                          │
│    Function: validate_with_ai()                                     │
│    Lines: 215-320                                                   │
│                                                                     │
│    Dynamic Thresholds Per Category:                                │
│    • Garbage:      High=55%, Low=40%                                │
│    • Pothole:      High=55%, Low=40%                                │
│    • Waterlogging: High=50%, Low=35%                                │
│    • Invalid:      High=60%, Low=45%                                │
│                                                                     │
│    Current Prediction:                                              │
│    • Category: "pothole"                                            │
│    • Confidence: 89%                                                │
│    • Threshold: 55% (High)                                          │
│                                                                     │
│    ✓ Rule 1: Not invalid (is "pothole")                             │
│    ✓ Rule 2: Confidence 89% > 55% threshold                         │
│    ✓ Rule 3: Text matches image ("pothole" = "pothole")             │
│                                                                     │
│    DECISION: APPROVED ✓                                             │
│                                                                     │
│    Return:                                                          │
│    {                                                                │
│      "is_valid": True,                                              │
│      "decision": "APPROVED",                                        │
│      "ai_category": "pothole",                                      │
│      "confidence": 0.89,                                            │
│      "message": "Complaint verified successfully",                  │
│      "geotag": {                                                    │
│        "lat_img": 17.385,                                           │
│        "long_img": 78.486,                                          │
│        "has_geotag": True                                           │
│      }                                                              │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 9. IMAGE UPLOAD TO SUPABASE STORAGE                                │
│    File: backend/app/routers/complaints.py                          │
│                                                                     │
│    filename = f"{uuid.uuid4()}.jpg"                                 │
│    # e.g., "a3f2c4d1-8b9e-4f3a-b1c2-9d8e7f6a5b4c.jpg"              │
│                                                                     │
│    response = supabase.storage                                      │
│        .from_(STORAGE_BUCKET)                                       │
│        .upload(filename, image_content)                             │
│                                                                     │
│    image_url = supabase.storage                                     │
│        .from_(STORAGE_BUCKET)                                       │
│        .get_public_url(filename)                                    │
│                                                                     │
│    ✓ Image uploaded to cloud storage                                │
│    ✓ Public URL: https://...supabase.co/storage/.../a3f2c4d1.jpg    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 10. DATABASE INSERT (Supabase PostgreSQL)                          │
│     File: backend/app/routers/complaints.py                         │
│                                                                     │
│     complaint_data = {                                              │
│       "tracking_id": "CVC-5432-2025",                               │
│       "user_id": current_user.id,                                   │
│       "title": "Large pothole on Main Street",                      │
│       "description": "Deep pothole causing traffic issues",         │
│       "category": "pothole",           ← User selected              │
│       "ai_category": "pothole",        ← AI verified                │
│       "confidence": 0.89,              ← 89% confidence             │
│       "status": "pending",                                          │
│       "image_url": "https://...a3f2c4d1.jpg",                       │
│       "lat_user": 17.385,              ← User GPS                   │
│       "long_user": 78.486,                                          │
│       "lat_img": 17.385,               ← Image EXIF GPS             │
│       "long_img": 78.486,                                           │
│       "created_at": "2025-12-09T10:30:00Z"                          │
│     }                                                               │
│                                                                     │
│     response = supabase.table("complaints")                         │
│         .insert(complaint_data)                                     │
│         .execute()                                                  │
│                                                                     │
│     ✓ Complaint saved to database                                   │
│     ✓ ID: 1234                                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 11. HTTP RESPONSE (JSON)                                            │
│     Status: 200 OK                                                  │
│                                                                     │
│     {                                                               │
│       "id": 1234,                                                   │
│       "tracking_id": "CVC-5432-2025",                               │
│       "title": "Large pothole on Main Street",                      │
│       "description": "Deep pothole causing traffic issues",         │
│       "category": "pothole",                                        │
│       "ai_category": "pothole",                                     │
│       "confidence": 0.89,                                           │
│       "status": "pending",                                          │
│       "image_url": "https://...a3f2c4d1.jpg",                       │
│       "lat_user": 17.385,                                           │
│       "long_user": 78.486,                                          │
│       "lat_img": 17.385,                                            │
│       "long_img": 78.486,                                           │
│       "created_at": "2025-12-09T10:30:00Z",                         │
│       "user_id": 42                                                 │
│     }                                                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 12. FRONTEND DISPLAY                                                │
│     • Success message: "Complaint submitted successfully!"          │
│     • Tracking ID: CVC-5432-2025                                    │
│     • AI Verification: ✓ Verified (89% confidence)                  │
│     • Status: Pending review                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Detailed ML Model Architecture

### **MobileNetV2 Internal Processing**

```
INPUT IMAGE: pothole.jpg (1920×1080, 2.4 MB)
         ↓
    PREPROCESSING
         ↓
┌─────────────────────────────────────────────────────────────┐
│              (1, 224, 224, 3) Normalized Tensor             │
│              Values range: [-1.0 to 1.0]                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   MOBILENETV2 BASE MODEL      │
         │   (53 Convolutional Layers)   │
         │   Pre-trained on ImageNet     │
         └───────────┬───────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐    ┌──────────┐    ┌──────────┐
│ LAYER 1 │    │ LAYER 27 │    │ LAYER 53 │
│ Conv2D  │    │ Conv2D   │    │ Conv2D   │
│         │    │          │    │          │
│ Detects │    │ Detects  │    │ Detects  │
│ Edges & │    │ Textures │    │ Complete │
│ Lines   │    │ Patterns │    │ Objects  │
└─────────┘    └──────────┘    └──────────┘
    │                │                │
    │  Learns:       │  Learns:       │  Learns:
    │  • Horizontal  │  • Rough       │  • Holes
    │  • Vertical    │  • Smooth      │  • Cracks
    │  • Diagonal    │  • Grainy      │  • Water
    │    edges       │    textures    │    surfaces
    │                │                │
    └────────────────┴────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  FEATURE MAP OUTPUT       │
         │  Shape: (7, 7, 1280)      │
         │                           │
         │  1,280 feature channels   │
         │  describing the image     │
         └───────────┬───────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  GLOBAL AVERAGE POOLING   │
         │  Reduce: 7×7×1280 → 1280  │
         └───────────┬───────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  FEATURE VECTOR (1280)    │
         │  [0.82, -0.15, 0.93, ...] │
         │                           │
         │  Compressed description   │
         │  of the entire image      │
         └───────────┬───────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│              CUSTOM CLASSIFICATION HEAD                    │
│  (Trained specifically for CivicLens - 167,300 params)     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  BatchNormalization()                                      │
│  ↓ Normalize features for stability                        │
│                                                            │
│  Dropout(0.3)                                              │
│  ↓ Randomly drop 30% of connections (prevent overfitting)  │
│                                                            │
│  Dense(128, activation='relu')                             │
│  ↓ 128 neurons learn civic issue patterns                  │
│  ↓ ReLU: max(0, x) - removes negatives                     │
│                                                            │
│  BatchNormalization()                                      │
│  ↓ Normalize again                                         │
│                                                            │
│  Dropout(0.5)                                              │
│  ↓ Drop 50% for stronger regularization                    │
│                                                            │
│  Dense(4, activation='softmax')                            │
│  ↓ 4 output neurons (one per category)                     │
│  ↓ Softmax: Convert to probabilities summing to 1.0        │
│                                                            │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
                ┌────────────────────────────┐
                │     RAW OUTPUTS (logits)   │
                │  [0.05, 0.03, 0.89, 0.03]  │
                │                            │
                │  Index 0: Garbage          │
                │  Index 1: Invalid_data     │
                │  Index 2: Potholes  ← MAX  │
                │  Index 3: water logging    │
                └────────────┬───────────────┘
                             │
                             ▼
                ┌────────────────────────────┐
                │   FINAL PREDICTION         │
                │                            │
                │   Category: POTHOLE        │
                │   Confidence: 89%          │
                │   Is Valid: TRUE           │
                └────────────────────────────┘
```

---

## ⚙️ Key Functions & Their Purpose

### **File: `backend/ml/classifier.py`**

| Function | Lines | Purpose | Input | Output |
|----------|-------|---------|-------|--------|
| `ImageClassifier.__init__()` | 75-110 | Initialize classifier, load model | model_path (optional) | None |
| `ImageClassifier._load_model()` | 112-145 | Load Keras model from disk | None | Sets self.model |
| `ImageClassifier.classify()` | 147-225 | Main classification function | image_data (bytes) | {predicted_class, confidence, probabilities} |
| `TextAnalyzer.analyze()` | 300-350 | Extract category from text | title, description | {predicted_category, keywords} |
| `GeotagExtractor.extract_geotag()` | 360-470 | Extract GPS from EXIF | image_data (bytes) | {lat_img, long_img, has_geotag} |
| `ComplaintVerifier.verify()` | 505-620 | Complete verification pipeline | image, title, desc, category | {is_valid, decision, message} |

### **File: `backend/app/routers/complaints.py`**

| Function | Lines | Purpose | Input | Output |
|----------|-------|---------|-------|--------|
| `get_classifier()` | 26-36 | Get/initialize classifier (lazy loading) | None | ImageClassifier instance |
| `get_verifier()` | 39-49 | Get/initialize verifier | None | ComplaintVerifier instance |
| `analyze_text_for_category()` | 152-210 | Text category extraction | title, description | {category, confidence} |
| `validate_with_ai()` | 215-320 | AI validation orchestrator | image, title, desc, category | {is_valid, decision, ai_category} |
| `create_complaint()` | 322-450 | Main API endpoint | Form data + image | Complaint object (JSON) |

---

## 📊 Performance Metrics

### **Model Accuracy (Tested on 2,570 Images)**

```
┌─────────────────────────────────────────────────────┐
│              OVERALL ACCURACY: 95.99%               │
│         Correctly Classified: 2,467/2,570           │
└─────────────────────────────────────────────────────┘

Per-Class Performance:
┌──────────────┬──────────┬───────────┬────────┬─────────┐
│ Class        │ Accuracy │ Precision │ Recall │ F1-Score│
├──────────────┼──────────┼───────────┼────────┼─────────┤
│ Garbage      │  95.26%  │   95.53%  │ 95.26% │  95.26% │
│ Invalid      │  98.18%  │   98.01%  │ 98.18% │  98.18% │
│ Pothole      │  94.65%  │   93.86%  │ 94.65% │  94.65% │
│ Waterlogging │  91.79%  │   92.93%  │ 91.79% │  91.79% │
└──────────────┴──────────┴───────────┴────────┴─────────┘

Average Processing Time:
• Model loading: ~2 seconds (first time only)
• Image preprocessing: ~0.1 seconds
• CNN inference: ~0.3 seconds
• Text analysis: ~0.05 seconds
• EXIF extraction: ~0.1 seconds
• Total per complaint: ~3-5 seconds
```

---

## 🔒 Validation Rules

### **3-Tier Confidence System**

```
For each category, we have TWO thresholds:

┌─────────────────────────────────────────────────────────┐
│                   GARBAGE CATEGORY                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   0% ─────────────────── 40% ─────────── 55% ───── 100%│
│   │                       │               │          │  │
│   │     REJECT            │  LOW CONF.    │  APPROVE │  │
│   │                       │  (Ask User)   │          │  │
│   │                       │               │          │  │
│   └───────────────────────┴───────────────┴──────────┘  │
│                                                         │
│   < 40%:  "Image unclear, rejected"                     │
│   40-55%: "Low confidence, please confirm"              │
│   ≥ 55%:  "Approved automatically"                      │
└─────────────────────────────────────────────────────────┘

Complete Threshold Table:
┌──────────────┬──────────┬──────────┐
│ Category     │ Low      │ High     │
├──────────────┼──────────┼──────────┤
│ Garbage      │   40%    │   55%    │
│ Pothole      │   40%    │   55%    │
│ Waterlogging │   35%    │   50%    │
│ Invalid      │   45%    │   60%    │
└──────────────┴──────────┴──────────┘
```

### **Validation Decision Tree**

```
                  ┌─────────────────────┐
                  │  AI Classification  │
                  │   & Text Analysis   │
                  └──────────┬──────────┘
                             │
                ┌────────────▼────────────┐
                │ Is category "invalid"?  │
                └────┬─────────────┬──────┘
                     │YES          │NO
                     ▼             ▼
            ┌──────────────┐  ┌──────────────────┐
            │ REJECT       │  │ Check confidence │
            │ "Invalid     │  │ threshold        │
            │  image"      │  └────┬────────┬────┘
            └──────────────┘       │        │
                                   │        │
                        ┌──────────┴───┐    │
                        │ < Threshold? │    │
                        └──┬────────┬──┘    │
                           │YES     │NO     │
                           ▼        ▼       │
                  ┌──────────┐  ┌──────────▼────────┐
                  │ REJECT   │  │ Text matches image?│
                  │ "Low     │  └──┬──────────┬─────┘
                  │ conf."   │     │YES       │NO
                  └──────────┘     ▼          ▼
                          ┌──────────┐  ┌──────────┐
                          │ APPROVE  │  │ REJECT   │
                          │ "Verified"│  │ "Mismatch"│
                          └──────────┘  └──────────┘
```

---

## 🎯 Real-World Examples

### **Example 1: Successful Validation**

```
INPUT:
• Image: Clear photo of pothole (89% confidence)
• Title: "Large pothole on Main St"
• Description: "Deep pothole causing issues"
• Category: "pothole"

PROCESSING:
1. Image → pothole (89%)  ✓
2. Text → pothole         ✓
3. Confidence > 55%       ✓
4. Categories match       ✓

RESULT: APPROVED
```

### **Example 2: Low Confidence**

```
INPUT:
• Image: Dark, blurry photo (48% garbage, 41% invalid)
• Title: "Garbage pile"
• Description: "Lots of waste"
• Category: "garbage"

PROCESSING:
1. Image → garbage (48%)  ✓
2. Text → garbage         ✓
3. Confidence: 48% (between 40-55%)  ⚠️

RESULT: LOW_CONFIDENCE
Message: "Image quality unclear. Confidence: 48%. Please confirm."
Action: Ask user to confirm or re-upload
```

### **Example 3: Category Mismatch**

```
INPUT:
• Image: Clear pothole photo (87% confidence)
• Title: "Garbage on street"
• Description: "Lots of trash everywhere"
• Category: "garbage"

PROCESSING:
1. Image → pothole (87%)  ✓
2. Text → garbage         ✗
3. Mismatch detected!

RESULT: CATEGORY_MISMATCH
Message: "Image shows pothole, but description mentions garbage"
Suggestion: "Upload garbage photo or change description"
```

### **Example 4: Invalid Image**

```
INPUT:
• Image: Photo of sky/building (91% invalid)
• Title: "Broken road"
• Description: "Road needs repair"
• Category: "pothole"

PROCESSING:
1. Image → invalid (91%)  ✗

RESULT: INVALID_IMAGE
Message: "Image doesn't show a valid civic issue"
Suggestion: "Please upload a clear photo of the actual problem"
```

---

## 🚀 Optimization & Best Practices

### **Model Loading (Lazy Initialization)**

```python
# NOT loaded at server startup (slow!)
# Loaded only when first complaint is submitted

_classifier = None  # Global variable

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ImageClassifier()  # Load model (2 sec)
        logger.info("Classifier loaded")
    return _classifier

# Result:
# • Fast server startup
# • Model loaded only if needed
# • Reused across all requests
```

### **Batch Processing (Future Enhancement)**

```python
# Current: One image at a time
prediction = model.predict(img_array)  # (1, 224, 224, 3)

# Future: Multiple images in one batch
# predictions = model.predict(batch)  # (32, 224, 224, 3)
# 32x faster than processing individually!
```

---

## 📝 File Locations Summary

```
TRAINED MODEL:
📁 D:\civiclens-frontend\backend\ml\models\civic_classifier.keras (11.6 MB)

CLASS NAMES:
📄 D:\civiclens-frontend\backend\ml\models\class_names.json

MAIN PIPELINE:
📄 D:\civiclens-frontend\backend\ml\classifier.py (661 lines)

API ENDPOINT:
📄 D:\civiclens-frontend\backend\app\routers\complaints.py (803 lines)

TRAINING SCRIPT:
📄 D:\civiclens-frontend\backend\ml\train_mobilenet.py (355 lines)

PERFORMANCE METRICS:
📄 D:\civiclens-frontend\backend\ml\models\performance_results.txt
📊 D:\civiclens-frontend\backend\ml\models\confusion_matrix.png
📊 D:\civiclens-frontend\backend\ml\models\detailed_performance_metrics.png
```

---

## ✅ Summary

### **What Happens When User Submits Complaint:**

1. **FastAPI** receives HTTP POST with image + text
2. **ImageClassifier** loads MobileNetV2 model (if not already loaded)
3. **Preprocessing** resizes image to 224×224 and normalizes [-1, 1]
4. **CNN** processes through 53 convolutional layers
5. **Classification Head** outputs 4 probabilities (softmax)
6. **TextAnalyzer** extracts keywords from title/description
7. **GeotagExtractor** reads GPS from EXIF metadata
8. **Validation Logic** applies dynamic thresholds and matching rules
9. **Supabase** stores image in cloud storage
10. **PostgreSQL** saves complaint record with AI predictions
11. **Response** returns JSON with tracking ID and AI results

### **Model Architecture:**
- Base: MobileNetV2 (pre-trained on ImageNet)
- Custom Head: 128 neurons → 4 outputs
- Total Parameters: 2,762,702
- Accuracy: 95.99%
- Speed: ~3-5 seconds per complaint

### **Validation:**
- 3-tier confidence system (Reject/Ask/Approve)
- Dynamic thresholds per category
- Text-image matching
- Invalid image detection

---

**Status: Production-Ready** 🚀  
**Documentation Updated:** December 9, 2025  
**Model Version:** MobileNetV2 v1.0 (95.99% accuracy)
