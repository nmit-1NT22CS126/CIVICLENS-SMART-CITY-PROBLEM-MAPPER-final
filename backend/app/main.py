from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, complaints, admin

app = FastAPI(
    title="CivicLens Backend",
    description="Civic Issue Reporting API powered by Supabase",
    version="2.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:5173",  # Vite Frontend
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "*"  # Allow all origins for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to CivicLens API",
        "version": "2.0.0",
        "database": "Supabase"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

