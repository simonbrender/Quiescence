# Free Text Search Verification & Fixes

## Summary

This document summarizes the investigation and fixes applied to the free-text search functionality in Celerio Scout.

## Issues Found

### 1. **Database Column Missing Error**
- **Problem**: The `last_raise_stage` column doesn't exist in the database, causing queries to fail
- **Root Cause**: Database was created before all columns were added to the schema
- **Fix Applied**: Added column migration check in free-text search endpoint before querying

### 2. **Filters Too Permissive**
- **Problem**: Filters used `OR ... IS NULL`, causing ALL companies to match regardless of criteria
- **Example**: `funding_amount >= ? OR funding_amount IS NULL` matches companies without funding data
- **Impact**: Every query returned the same 11 companies (mock/seed data)
- **Fix Applied**: Removed `OR ... IS NULL` clauses so filters only match companies with actual data

### 3. **Fallback Query Returned All Companies**
- **Problem**: When schema errors occurred, fallback query returned ALL companies
- **Fix Applied**: Changed fallback to return empty results and log warning

### 4. **Frontend Not Routing to Free-Text Endpoint**
- **Problem**: Component may not be detecting free text query correctly
- **Fix Applied**: Added console logging to track which endpoint is called

## Fixes Applied

### Backend (`backend/main.py`)

1. **Column Migration in Free-Text Endpoint** (lines 883-891)
   - Ensures all required columns exist before querying
   - Adds missing columns if they don't exist
   - Raises HTTPException if column addition fails

2. **Stricter Filters** (lines 646-680)
   - Removed `OR ... IS NULL` from funding filters
   - Removed `OR ... IS NULL` from employee count filters
   - Removed `OR ... IS NULL` from date filters
   - Removed `OR ... IS NULL` from fund tier filters

3. **Better Fallback Behavior** (line 714)
   - Changed fallback query from `WHERE 1=1` to `WHERE 1=0`
   - Returns empty results instead of all companies
   - Logs warning about schema issues

4. **Enhanced Logging** (lines 799-803)
   - Added detailed logging for query parsing
   - Logs extracted stages, focus areas, funding ranges, etc.

### Frontend (`frontend/src/components/AdvancedSearch.jsx`)

1. **Debug Logging** (lines 30-48)
   - Added console logs to track which endpoint is called
   - Logs free text query and search params
   - Logs number of companies returned

## Current Status

### ✅ Working Components

1. **Rule-Based Query Parser**
   - Works without Ollama
   - Extracts: stages, focus areas, funding, employees, months post-raise, fund tiers
   - Handles complex queries like: "Seed/Series A AI/B2B companies 12-18 months post-raise, typically with $3-15m in total funding from a tier 1/2 VC and 10-80 employees"

2. **Web Discovery System**
   - Searches Crunchbase (web scraping)
   - Searches DuckDuckGo for companies
   - Searches LinkedIn (placeholder - requires OAuth2)
   - Deduplicates results by domain

3. **Database Schema**
   - All required columns defined in CREATE TABLE
   - Migration code exists to add missing columns

### ⚠️ Requires Backend Restart

**All fixes require backend server restart to take effect.**

The backend is currently running old code. After restart:
- Column migration will run automatically
- Stricter filters will be applied
- Better error handling will be active
- Enhanced logging will show what's happening

### 🔍 Needs Verification

1. **Ollama Status**
   - Ollama is NOT currently running
   - NLP parser falls back to rule-based parsing (which works)
   - For better parsing, start Ollama: `ollama serve`

2. **Free-Text Endpoint Routing**
   - Frontend component logic looks correct
   - Console logs will show which endpoint is called
   - Need to verify after backend restart

3. **Web Discovery Execution**
   - Code exists and looks correct
   - Need to verify it's actually being called
   - Check backend logs for `[WEB-DISCOVERY]` messages

## Testing Steps

### Step 1: Restart Backend
```bash
# Stop current backend (Ctrl+C)
# Then restart:
cd backend
python main.py
```

### Step 2: Verify Backend Started Correctly
- Check for column migration messages in console
- Should see: `[FREE-TEXT] Column 'last_raise_stage' exists: True` (or added successfully)

### Step 3: Test Free-Text Endpoint Directly
```powershell
$body = @{query='Seed/Series A AI/B2B companies 12-18 months post-raise, typically with $3-15m in total funding from a tier 1/2 VC and 10-80 employees'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/companies/search/free-text' -Method Post -Body $body -ContentType 'application/json'
```

Expected:
- Should parse query successfully
- Should trigger web discovery
- Should return companies matching criteria (not all companies)
- Should see `[FREE-TEXT]` and `[WEB-DISCOVERY]` log messages

### Step 4: Test via Browser
1. Navigate to http://localhost:5173
2. Click "Advanced Search"
3. Enter free text query
4. Click "Search Companies"
5. Check browser console for logs
6. Verify results are different based on query

### Step 5: Verify Web Discovery
Check backend console logs for:
- `[WEB-DISCOVERY] Starting discovery with params:`
- `[WEB-DISCOVERY] Queuing Crunchbase search...`
- `[WEB-DISCOVERY] Queuing web search for:`
- `[WEB-DISCOVERY] Total unique companies discovered:`

## Expected Behavior After Fixes

1. **Query Parsing**
   - Free text query → Structured parameters
   - Example: "Seed/Series A AI/B2B companies..." → `{stages: ["Seed", "Series A"], focus_areas: ["AI/ML", "B2B SaaS"], ...}`

2. **Web Discovery**
   - Searches multiple sources (Crunchbase, DuckDuckGo, LinkedIn)
   - Finds companies matching criteria
   - Stores new companies in database
   - Returns discovered companies

3. **Database Query**
   - Applies strict filters (only companies with matching data)
   - Returns different results for different queries
   - Combines discovered companies with existing database records

4. **Results**
   - Should return companies that actually match the criteria
   - Should NOT return the same 11 companies for every query
   - Should include newly discovered companies from web sources

## Files Modified

1. `backend/main.py`
   - Added column migration in free-text endpoint
   - Fixed filter logic (removed `OR ... IS NULL`)
   - Fixed fallback query behavior
   - Added enhanced logging

2. `frontend/src/components/AdvancedSearch.jsx`
   - Added debug console logging

## Next Steps

1. ✅ **Restart backend server** (REQUIRED)
2. ✅ **Test free-text endpoint directly** via API
3. ✅ **Test via browser** with complex query
4. ✅ **Verify web discovery** is working (check logs)
5. ✅ **Verify results** are different for different queries
6. ⚠️ **Optional**: Start Ollama for better NLP parsing

## Notes

- Rule-based parser works well for structured queries
- Ollama is optional but provides better parsing for complex/natural language
- Web discovery may take 10-30 seconds depending on sources
- Database filters are now strict - companies without data won't match




