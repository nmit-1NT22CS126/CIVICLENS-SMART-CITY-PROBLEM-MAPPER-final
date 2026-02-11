# Admin Completion Image Upload - Testing Guide

## Feature Overview
The admin portal includes a feature to upload "after" images when work is completed, with AI-powered verification to ensure the issue was actually resolved.

## ✅ Implementation Status

### Frontend (`AdminComplaintDetail.jsx`)
✅ **State Management**
- `afterImage` - Stores uploaded file
- `afterImagePreview` - Preview display
- `verificationResult` - AI verification result

✅ **File Upload**
- `handleFileChange()` - Processes image selection
- Creates preview for user
- Clears previous verification results

✅ **AI Verification**
- `handleVerifyCompletion()` - Sends image to backend
- Displays verification results with:
  - Decision (VERIFIED / NOT_VERIFIED / ERROR)
  - Confidence score
  - Location match percentage
  - Before/After classification
  - Visual similarity metrics

✅ **UI Display**
- Shows "after" image if already uploaded
- File input for new uploads
- "Verify Completion" button
- Color-coded result display (green/red/yellow)
- Detailed verification metrics
- Auto-updates complaint status to "Resolved" on success

### Backend (`complaints.py`)
✅ **API Endpoint**: `POST /api/complaints/{complaint_id}/verify-completion`
- ✅ Accepts `after_image` file upload
- ✅ Requires authentication (admin/worker)
- ✅ Downloads original complaint image from Supabase
- ✅ Runs AI verification comparison
- ✅ Uploads after image to storage on success
- ✅ Updates database with:
  - `after_image_url`
  - `verification_confidence`
  - `verified_at`
  - `verified_by`
  - `status` → "Resolved" (if verified)
- ✅ Creates admin log entry
- ✅ Returns detailed verification result

### ML Module (`verify_completion.py`)
✅ **WorkCompletionVerifier Class**
- ✅ Feature extraction using MobileNetV2
- ✅ Location similarity check (70% threshold)
- ✅ Issue classification (before/after)
- ✅ Visual difference detection
- ✅ Multi-stage decision logic:
  - Same location verification
  - Issue resolution check
  - Visual change detection

### Database Schema
✅ **New Columns Added** (via `migration_verification.sql`):
- `after_image_url` - URL of completion image
- `verification_confidence` - AI confidence (0.0-1.0)
- `verified_at` - Timestamp
- `verified_by` - Reference to user who verified

## 🧪 How to Test

### Prerequisites
1. ✅ Backend running on port 8000
2. ✅ Frontend running on port 5173
3. ✅ Admin account logged in
4. ✅ At least one complaint with status "In Progress" or "Under Review"
5. ✅ Database migration applied (`migration_verification.sql`)

### Step-by-Step Test

#### 1. Navigate to Complaint Detail
```
1. Login as admin
2. Go to Admin Dashboard
3. Click on any complaint
4. Scroll to "Work Completion Verification" section
```

#### 2. Upload After Image
```
1. Click "Take/Upload Photo" button
2. Select an image showing the completed work
3. Preview should appear below button
4. Button text changes to "Change Photo"
```

#### 3. Verify with AI
```
1. Click "Verify Completion" button
2. Wait for AI processing (shows "Verifying with AI...")
3. Result appears below:
   - ✅ Green: Work verified successfully
   - ❌ Red: Verification failed
   - ⚠️ Yellow: Error occurred
```

#### 4. Check Results
**If Verified (Green):**
- Message: "Work completed successfully! Location matches and issue appears resolved."
- Confidence: Shows percentage (e.g., 85.3%)
- Location Match: Shows similarity (e.g., 92.1%)
- Status automatically updated to "Resolved"
- After image saved to database

**If Not Verified (Red):**
- Message explains why (e.g., "Location mismatch" or "Issue still present")
- Shows diagnostic details
- Status remains unchanged
- Admin can upload different image

**If Error (Yellow):**
- Shows error message
- Admin can retry

## 🔍 Verification Logic

### Stage 1: Location Check
- Extracts features from both images using MobileNetV2
- Calculates cosine similarity
- **Pass**: ≥70% similar → Same location
- **Fail**: <70% → Different location (rejected)

### Stage 2: Issue Resolution
**Before Image:**
- Must show civic issue (Garbage/Pothole/Waterlogging)
- If shows "Invalid" → Can't verify (no issue)

**After Image:**
- Should show normal/fixed state (Invalid/Invalid_data)
- OR different issue category
- If same issue still present → Not resolved (rejected)

### Stage 3: Visual Change
- Compares pixel-level differences
- Significant change expected (<50% similarity)
- If too similar → No work done (rejected)

### Decision Outcomes
1. **VERIFIED** - All checks passed
2. **LOCATION_MISMATCH** - Different location
3. **ISSUE_UNRESOLVED** - Same issue still visible
4. **NO_CHANGE** - Images too similar
5. **NO_ISSUE_DETECTED** - Original had no issue
6. **ERROR** - Processing failed

## 📊 Expected Results

### Test Case 1: Valid Completion
**Before**: Pothole image  
**After**: Fixed road image (same location)  
**Expected**: ✅ VERIFIED, Status → Resolved

### Test Case 2: Wrong Location
**Before**: Pothole at Location A  
**After**: Fixed road at Location B  
**Expected**: ❌ LOCATION_MISMATCH, Status unchanged

### Test Case 3: Issue Still Present
**Before**: Garbage pile  
**After**: Same garbage pile  
**Expected**: ❌ ISSUE_UNRESOLVED, Status unchanged

### Test Case 4: No Work Done
**Before**: Pothole image  
**After**: Same pothole (identical photo)  
**Expected**: ❌ NO_CHANGE, Status unchanged

## 🐛 Troubleshooting

### Upload Button Not Appearing
- Check complaint status (should be "In Progress" or "Under Review")
- Verify admin is logged in
- Check browser console for errors

### "Complaint has no before image" Error
- Original complaint missing image
- Use different complaint with image

### Verification Always Fails
- Check image quality (clear, well-lit)
- Ensure before/after are from same location
- Check backend logs: `backend/app.log`

### AI Service Unavailable (503)
- ML model not loaded
- Check: `backend/ml/verify_completion.py`
- Verify model files exist:
  - `backend/ml/models/civic_classifier.keras`
  - `backend/ml/models/class_names.json`

### Database Update Fails
- Migration not applied
- Run: `migration_verification.sql` in Supabase
- Check columns exist:
  ```sql
  SELECT column_name 
  FROM information_schema.columns 
  WHERE table_name = 'complaints' 
  AND column_name IN ('after_image_url', 'verification_confidence', 'verified_at', 'verified_by');
  ```

## 🔧 Configuration

### Similarity Thresholds (in `verify_completion.py`)
```python
LOCATION_SIMILARITY_THRESHOLD = 0.70  # 70% = same location
SIGNIFICANT_CHANGE_THRESHOLD = 0.50   # <50% = work done
```

**Adjust if:**
- Too many false positives → Increase thresholds
- Too many false negatives → Decrease thresholds

### Image Upload Settings
- Max file size: Configured in backend
- Accepted formats: JPEG, PNG
- Compression: Automatic on upload

## ✅ Verification Checklist

- [ ] Backend server running
- [ ] ML model loaded successfully
- [ ] Database migration applied
- [ ] Admin logged in
- [ ] Navigate to complaint detail page
- [ ] "Work Completion Verification" section visible
- [ ] "Take/Upload Photo" button clickable
- [ ] Image upload shows preview
- [ ] "Verify Completion" button appears
- [ ] Clicking button triggers AI verification
- [ ] Results display with confidence scores
- [ ] Verified complaints auto-update to "Resolved"
- [ ] After image appears in complaint details
- [ ] Admin log entry created

## 📝 Summary

**Status**: ✅ **FULLY IMPLEMENTED**

The admin completion image upload feature is fully functional with:
1. ✅ File upload with preview
2. ✅ AI-powered verification
3. ✅ Before/after image comparison
4. ✅ Location similarity check
5. ✅ Issue resolution detection
6. ✅ Automatic status updates
7. ✅ Database persistence
8. ✅ Detailed result display
9. ✅ Error handling
10. ✅ Admin logging

**Next Steps**: User testing to validate real-world performance and adjust thresholds if needed.
