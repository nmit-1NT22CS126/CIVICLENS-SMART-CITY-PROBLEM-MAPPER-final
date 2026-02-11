# 🚀 CivicLens Quick Start Guide

## ✅ SOLUTION FOR "Unable to connect to server" Error

The issue was caused by **multiple conflicting backend processes** running on port 8000.

### Fixed! Now you can:

1. **Test the system:**
   ```powershell
   .\DIAGNOSE.ps1
   ```

2. **If you see connection errors, run:**
   ```powershell
   .\FIX_CONNECTION.ps1
   ```

3. **Login at:** http://localhost:5173

---

## 📋 Quick Commands

### Start Services (First Time / After Restart)

**Terminal 1 - Backend:**
```powershell
.\START_BACKEND.ps1
```

**Terminal 2 - Frontend:**
```powershell
.\START_FRONTEND.ps1
```

### Troubleshooting

```powershell
# Check system status
.\DIAGNOSE.ps1

# Fix connection issues
.\FIX_CONNECTION.ps1

# Test Supabase connection
& "D:\civiclens-frontend\backend\venv\Scripts\python.exe" test-supabase.py

# Kill all processes on port 8000
netstat -ano | findstr ":8000"
# Then: Stop-Process -Id <PID> -Force
```

---

## ⚠️ Common Issues & Solutions

### Issue: "Unable to connect to server"
**Solution:** Run `.\FIX_CONNECTION.ps1`

### Issue: Multiple backend instances
**Solution:** Kill all processes on port 8000, then restart with `.\START_BACKEND.ps1`

### Issue: Login returns 500 error
**Solution:** Check Supabase connection with `python test-supabase.py`

### Issue: Frontend not loading
**Solution:** Run `.\START_FRONTEND.ps1` in a new terminal

---

## 📌 Important Notes

- **Always run backend and frontend in SEPARATE terminals**
- **Backend must be running BEFORE you try to login**
- **Default URLs:**
  - Frontend: http://localhost:5173
  - Backend: http://localhost:8000
- **If you see errors, run `.\DIAGNOSE.ps1` first**

---

## 🎯 Current Status

✅ Backend: Running on port 8000
✅ Frontend: Running on port 5173  
✅ Supabase: Connected
✅ Login endpoint: Working

**You can now login successfully!**
