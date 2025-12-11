# Fix: Failed to Load Portfolios

## Problem
The frontend is showing "Failed to load portfolios" because the backend server is not running.

## Solution

### Step 1: Start Backend Server

Open a new terminal and run:

```bash
cd C:\Users\simon\Repos\Quiescence\backend
python main.py
```

The backend should start on `http://localhost:8000`

### Step 2: Verify Backend is Running

Check that the backend is responding:

```bash
# In another terminal
curl http://localhost:8000/stats
```

Or open in browser: http://localhost:8000/docs

### Step 3: Refresh Frontend

Once backend is running, refresh the frontend (http://localhost:5173) and the portfolios should load.

## Root Cause

The `PortfolioSelector` component calls `getPortfoliosFiltered()` which makes a GET request to `/portfolios`. When the backend is not running, this request fails and shows "Failed to load portfolios".

## API Endpoint

The `/portfolios` endpoint is defined in `backend/main.py` at line 2246:

```python
@app.get("/portfolios", response_model=List[PortfolioInfo])
async def get_portfolios(
    stage: Optional[str] = None,
    focus_area: Optional[str] = None,
    vc_type: Optional[str] = None
):
```

This endpoint queries the `vcs` table and returns all VCs/portfolios.

## Quick Fix

If you need to start both frontend and backend:

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173



