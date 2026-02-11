from fastapi import APIRouter, HTTPException, status
from .. import schemas, auth
from ..supabase_client import supabase
from datetime import timedelta

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate):
    """Register a new user"""
    # Check if email already exists
    existing_user = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing_user.data:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = auth.get_password_hash(user.password)
    
    # Determine role (first user is admin for demo purposes)
    users_count = supabase.table("users").select("id", count="exact").execute()
    role = "admin" if users_count.count == 0 else "user"
    
    # Insert new user into Supabase
    new_user_data = {
        "name": user.name,
        "email": user.email,
        "password_hash": hashed_password,
        "role": role
    }
    
    response = supabase.table("users").insert(new_user_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to register user")
    
    return response.data[0]

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin):
    """Login user and return JWT token"""
    # Fetch user from Supabase
    response = supabase.table("users").select("*").eq("email", user_credentials.email).execute()
    
    if not response.data:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    
    user = response.data[0]
    
    # Verify password
    if not auth.verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(status_code=403, detail="Invalid credentials")
    
    # Create access token
    access_token = auth.create_access_token(
        data={"sub": user["email"], "role": user["role"], "user_id": user["id"]},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "user_id": user["id"]
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: dict = auth.Depends(auth.get_current_user)):
    """Get current logged-in user info"""
    return current_user


@router.post("/register-admin", response_model=schemas.UserResponse)
def register_admin(user: schemas.UserCreate, admin_secret: str = None):
    """Register a new admin user (requires admin secret)"""
    # Simple admin secret for demo - in production, use proper admin management
    ADMIN_SECRET = "civiclens-admin-2024"
    
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    # Check if email already exists
    existing_user = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing_user.data:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = auth.get_password_hash(user.password)
    
    # Insert new admin user
    new_user_data = {
        "name": user.name,
        "email": user.email,
        "password_hash": hashed_password,
        "role": "admin"
    }
    
    response = supabase.table("users").insert(new_user_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to register admin")
    
    return response.data[0]


@router.put("/promote-admin/{email}")
def promote_to_admin(email: str, admin_secret: str = None):
    """Promote existing user to admin (requires admin secret)"""
    ADMIN_SECRET = "civiclens-admin-2024"
    
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    # Find user by email
    user_response = supabase.table("users").select("*").eq("email", email).execute()
    
    if not user_response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update role to admin
    response = supabase.table("users").update({"role": "admin"}).eq("email", email).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to promote user")
    
    return {"message": f"User {email} has been promoted to admin", "user": response.data[0]}


@router.put("/reset-password/{email}")
def reset_password(email: str, new_password: str, admin_secret: str = None):
    """Reset user password (admin utility - requires admin secret)"""
    ADMIN_SECRET = "civiclens-admin-2024"
    
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    # Find user by email
    user_response = supabase.table("users").select("*").eq("email", email).execute()
    
    if not user_response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password and update
    hashed_password = auth.get_password_hash(new_password)
    response = supabase.table("users").update({"password_hash": hashed_password}).eq("email", email).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to reset password")
    
    return {"message": f"Password reset successfully for {email}"}

