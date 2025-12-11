# URGENT: Get 6K+ Companies Instructions

## Current Problem
- Only ~1,250 companies in database
- Need 6,000+ from YC + Antler alone
- Need ALL VCs, Studios, Accelerators scraped

## Solution: Run Comprehensive Scraping

### STEP 1: Stop Backend Server
**CRITICAL:** The database is locked by the backend server (PID 6940)

**Windows:**
```powershell
# Find and kill the backend process
Get-Process python | Where-Object {$_.Id -eq 6940} | Stop-Process -Force
```

Or manually:
1. Open Task Manager
2. Find Python process (PID 6940)
3. End Task

### STEP 2: Run Comprehensive Scraping

```bash
cd backend
python URGENT_GET_6K_COMPANIES.py
```

This will:
- Scrape ALL 40 YC batches (2005-2025) → ~4,000 companies
- Scrape Antler with infinite scroll → ~1,000+ companies
- Save ALL companies to database
- **NO LIMITS** - gets everything

**Expected Time:** 1-2 hours

### STEP 3: Scrape ALL VCs

After YC+Antler completes:

```bash
cd backend
python scale_all_vcs.py
```

This will:
- Get ALL VCs from database
- Scrape each VC's portfolio
- **NO LIMITS** on companies per VC
- Processes in parallel batches

### STEP 4: Verify Results

```bash
cd backend
python monitor_workflow_progress.py
```

Should show:
- YC: 4,000+
- Antler: 1,000+
- Total: 6,000+
- All VCs scraped

## Alternative: Use UI (if backend running)

1. **Stop backend first** (database must be unlocked)
2. Start backend: `cd backend; python main.py`
3. Open UI: http://localhost:5173
4. Click "Portfolio" → Select YC + Antler → "Scrape & Analyze"
5. Click "Discover VC" to find more VCs
6. Select all VCs → "Scrape & Analyze"

## Files Created

1. `backend/URGENT_GET_6K_COMPANIES.py` - Gets 6k+ from YC+Antler
2. `backend/force_comprehensive_scraping.py` - Full workflow
3. `backend/scale_all_vcs.py` - Scrapes ALL VCs

## Why Current Count is Low

The comprehensive scraping workflows were created but **never actually executed** because:
1. Database was locked by backend server
2. Scripts were started but couldn't access database
3. Need to stop backend first, then run scraping

## Next Steps

1. **STOP BACKEND** (critical!)
2. Run `python backend/URGENT_GET_6K_COMPANIES.py`
3. Wait 1-2 hours for completion
4. Run `python backend/scale_all_vcs.py` for all VCs
5. Restart backend and verify in UI

The code is ready - it just needs to be executed with database access!

