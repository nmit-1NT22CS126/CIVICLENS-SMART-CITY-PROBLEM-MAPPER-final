from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .. import schemas, auth
from ..supabase_client import supabase
from datetime import datetime

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/reports", response_model=List[schemas.ComplaintResponse])
def get_all_reports(current_user: dict = Depends(auth.get_current_admin)):
    """Get all complaints (Admin only)"""
    response = supabase.table("complaints").select("*").order("created_at", desc=True).execute()
    return response.data if response.data else []

@router.get("/report/{id}", response_model=schemas.ComplaintResponse)
def get_report_detail(id: int, current_user: dict = Depends(auth.get_current_admin)):
    """Get single complaint details (Admin only)"""
    response = supabase.table("complaints").select("*").eq("id", id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return response.data[0]

@router.put("/report/{id}/status", response_model=schemas.ComplaintResponse)
def update_status(
    id: int,
    status_update: schemas.ComplaintStatusUpdate,
    current_user: dict = Depends(auth.get_current_admin)
):
    """Update complaint status (Admin only)"""
    # Validate status value - support multiple formats
    valid_statuses = ["Pending", "In-Review", "In Progress", "Resolved", "Rejected"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    update_data = {
        "status": status_update.status,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("complaints").update(update_data).eq("id", id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found or update failed")
    
    return response.data[0]

@router.post("/report/{id}/note", response_model=schemas.AdminLogResponse)
def add_admin_note(
    id: int,
    note: schemas.AdminNoteCreate,
    current_user: dict = Depends(auth.get_current_admin)
):
    """Add admin note to complaint log (Admin only)"""
    # Verify complaint exists
    complaint_check = supabase.table("complaints").select("id").eq("id", id).execute()
    if not complaint_check.data:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Insert admin log
    log_data = {
        "complaint_id": id,
        "admin_id": current_user["id"],
        "message": note.message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("admin_logs").insert(log_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to add note")
    
    return response.data[0]

@router.get("/report/{id}/notes", response_model=List[schemas.AdminLogResponse])
def get_admin_notes(id: int, current_user: dict = Depends(auth.get_current_admin)):
    """Get all admin notes for a complaint (Admin only)"""
    response = supabase.table("admin_logs").select("*").eq("complaint_id", id).order("timestamp", desc=True).execute()
    return response.data if response.data else []

@router.get("/map", response_model=List[schemas.ComplaintResponse])
def get_map_data(current_user: dict = Depends(auth.get_current_admin)):
    """Get all complaints for map visualization (Admin only)"""
    response = supabase.table("complaints").select("*").execute()
    return response.data if response.data else []

@router.get("/stats")
def get_dashboard_stats(current_user: dict = Depends(auth.get_current_admin)):
    """Get dashboard statistics (Admin only)"""
    # Get total complaints
    total = supabase.table("complaints").select("id", count="exact").execute()
    
    # Get counts by status
    pending = supabase.table("complaints").select("id", count="exact").eq("status", "Pending").execute()
    in_review = supabase.table("complaints").select("id", count="exact").eq("status", "In-Review").execute()
    resolved = supabase.table("complaints").select("id", count="exact").eq("status", "Resolved").execute()
    
    return {
        "total": total.count or 0,
        "pending": pending.count or 0,
        "in_review": in_review.count or 0,
        "resolved": resolved.count or 0
    }

