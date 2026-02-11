# Test Supabase Connection
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
env_path = Path(__file__).parent / 'backend' / '.env'
load_dotenv(dotenv_path=env_path)

print("Testing Supabase Connection...")
print(f"ENV file path: {env_path}")
print(f"ENV file exists: {env_path.exists()}")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"\nSupabase URL: {SUPABASE_URL}")
print(f"Supabase Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "None")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ ERROR: Supabase credentials not found in .env file")
    exit(1)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("\n✓ Supabase client created successfully")
    
    # Test connection by querying users table
    response = supabase.table("users").select("id").limit(1).execute()
    print(f"✓ Successfully connected to Supabase")
    print(f"✓ Users table is accessible (found {len(response.data)} records)")
    
except Exception as e:
    print(f"\n❌ ERROR connecting to Supabase: {e}")
    exit(1)

print("\n✓ All tests passed!")
