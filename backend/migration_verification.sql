-- ============================================
-- CivicLens - Work Completion Verification Migration
-- Run this SQL in your Supabase SQL Editor
-- ============================================

-- Add new columns for work completion verification
ALTER TABLE public.complaints ADD COLUMN IF NOT EXISTS after_image_url TEXT;
ALTER TABLE public.complaints ADD COLUMN IF NOT EXISTS verification_confidence DOUBLE PRECISION;
ALTER TABLE public.complaints ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;
ALTER TABLE public.complaints ADD COLUMN IF NOT EXISTS verified_by BIGINT REFERENCES public.users(id) ON DELETE SET NULL;

-- Add index for verification queries
CREATE INDEX IF NOT EXISTS idx_complaints_verified_at ON public.complaints(verified_at);
CREATE INDEX IF NOT EXISTS idx_complaints_verified_by ON public.complaints(verified_by);

-- Update existing Resolved complaints to have verification timestamp
UPDATE public.complaints 
SET verified_at = updated_at 
WHERE status = 'Resolved' AND verified_at IS NULL;

COMMENT ON COLUMN public.complaints.after_image_url IS 'URL of the after-completion image uploaded by worker';
COMMENT ON COLUMN public.complaints.verification_confidence IS 'AI confidence score for work completion verification (0.0 to 1.0)';
COMMENT ON COLUMN public.complaints.verified_at IS 'Timestamp when work completion was verified';
COMMENT ON COLUMN public.complaints.verified_by IS 'ID of user (admin/worker) who verified the completion';
