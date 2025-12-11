# Fix: Network Error on Discover VCs

## Problem
Getting "Network Error" when clicking "Discover VCs" button.

## Root Causes

1. **Backend not running** - Most common cause
2. **Request timeout** - Discovery can take 5+ minutes, default timeout may be too short
3. **CORS issues** - Less likely but possible
4. **Backend endpoint error** - Discovery process failing

## Fixes Applied

### 1. Frontend Error Handling (`frontend/src/services/api.js`)
- ✅ Added 5-minute timeout for discovery endpoint
- ✅ Better error detection (ECONNREFUSED, timeout, etc.)
- ✅ Clear error messages for each error type

### 2. Frontend Component (`frontend/src/components/PortfolioSelector.jsx`)
- ✅ Improved error message display
- ✅ Shows specific error details
- ✅ Console logging for debugging

### 3. Backend Endpoint (`backend/main.py`)
- ✅ Added try-catch with proper error handling
- ✅ Returns HTTPException with detailed error message
- ✅ Logs errors for debugging

## How to Test

### Step 1: Ensure Backend is Running
```bash
cd backend
python main.py
```

### Step 2: Test Discovery Endpoint Directly
```bash
# In another terminal
python backend/test_portfolios_endpoint.py
```

### Step 3: Test in Frontend
1. Open http://localhost:5173
2. Click "Portfolio" button
3. Click "Discover VCs" button
4. Should see:
   - Loading indicator ("Discovering...")
   - Success message with count
   - OR clear error message if something fails

## Expected Behavior

### When Backend is Running:
- Shows "Discovering..." spinner
- Takes 1-5 minutes (discovery crawls multiple websites)
- Shows success: "Discovered X VCs, added Y new ones"
- Refreshes portfolio list

### When Backend is NOT Running:
- Shows error: "Backend server is not running. Please start it with: python backend/main.py"

### When Request Times Out:
- Shows error: "Discovery request timed out. This may take several minutes. Please try again."

### When Discovery Fails:
- Shows error with details from backend
- Logs full error to console

## Troubleshooting

1. **Check Backend Logs:**
   - Look for errors in backend terminal
   - Check for timeout errors
   - Check for web scraping errors

2. **Check Browser Console:**
   - Open DevTools (F12)
   - Check Network tab for failed requests
   - Check Console for error messages

3. **Test Endpoint Directly:**
   ```bash
   curl -X POST http://localhost:8000/portfolios/discover
   ```

## Notes

- Discovery can take 5-10 minutes (crawls multiple websites)
- Some websites may timeout (expected behavior)
- Discovery may return 0 VCs if all sources timeout
- This is normal - discovery is best-effort



