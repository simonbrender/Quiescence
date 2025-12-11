"""
Celerio Scout - Backend API
OSINT-powered startup stall detection engine
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import List, Optional
import duckdb
import json
import os
import asyncio
import threading
from pathlib import Path
from datetime import datetime, timedelta, date
from urllib.parse import urlparse
from scorer import calculate_scores, scan_company
from seeds import load_mock_data
from portfolio_scraper import PortfolioScraper
from vc_discovery import VCDiscovery
try:
    from data_enrichment import enrich_company_data
except ImportError:
    # Fallback if data_enrichment not available
    async def enrich_company_data(company, domain):
        return company

app = FastAPI(title="Celerio Scout API", version="1.0.0")

# Import portfolio scraping monitor routes
from portfolio_scraping_monitor import router as portfolio_monitor_router
app.include_router(portfolio_monitor_router, prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DuckDB
# #region agent log
import json as debug_json
import threading
debug_log_path = r"c:\Users\simon\Repos\Quiescence\.cursor\debug.log"
def debug_log(location, message, data, hypothesis_id, session_id="debug-session", run_id="run1"):
    try:
        log_entry = {
            "id": f"log_{int(__import__('time').time() * 1000)}_{__import__('secrets').token_hex(4)}",
            "timestamp": int(__import__('time').time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id
        }
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(debug_json.dumps(log_entry) + '\n')
    except: pass
debug_log("main.py:39", "Database connection created", {"thread_id": threading.current_thread().ident, "connection_type": "module_level"}, "A")
# #endregion
conn = duckdb.connect("celerio_scout.db")

# Initialize database schema
conn.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY,
        name TEXT,
        domain TEXT,
        yc_batch TEXT,
        source TEXT,
        messaging_score REAL,
        motion_score REAL,
        market_score REAL,
        stall_probability TEXT,
        signals TEXT,
        funding_amount REAL,
        funding_currency TEXT DEFAULT 'USD',
        employee_count INTEGER,
        last_raise_date DATE,
        last_raise_stage TEXT,
        fund_tier TEXT,
        focus_areas TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
""")

# Add missing columns for existing databases (DuckDB doesn't support IF NOT EXISTS in ALTER TABLE)
# Check which columns exist and add missing ones
def column_exists(table_name, column_name):
    """Check if a column exists in a table by querying INFORMATION_SCHEMA"""
    try:
        # #region agent log
        debug_log("main.py:90", "column_exists check", {"table": table_name, "column": column_name}, "B")
        # #endregion
        # Use DuckDB's information schema to check column existence
        result = conn.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """).fetchone()
        exists = result is not None
        # #region agent log
        debug_log("main.py:90", "column_exists result", {"table": table_name, "column": column_name, "exists": exists}, "B")
        # #endregion
        return exists
    except Exception as e:
        # Fallback: try SELECT approach
        try:
            # #region agent log
            debug_log("main.py:90", "column_exists fallback: trying SELECT", {"table": table_name, "column": column_name}, "B")
            # #endregion
            result = conn.execute(f"SELECT {column_name} FROM {table_name} LIMIT 1").fetchone()
            # #region agent log
            debug_log("main.py:90", "column_exists: column found (SELECT)", {"table": table_name, "column": column_name}, "B")
            # #endregion
            return True
        except Exception as e2:
            # #region agent log
            debug_log("main.py:90", "column_exists: column NOT found", {"table": table_name, "column": column_name, "error": str(e2)[:100]}, "B")
            # #endregion
            return False

# List of columns that should exist
required_columns = [
    ('last_raise_stage', 'TEXT'),
    ('last_raise_date', 'DATE'),
    ('fund_tier', 'TEXT'),
    ('focus_areas', 'TEXT'),
    ('funding_amount', 'REAL'),
    ('funding_currency', 'TEXT'),
    ('employee_count', 'INTEGER')
]

# #region agent log
debug_log("main.py:118", "Starting column migration", {"required_columns_count": len(required_columns), "columns": [c[0] for c in required_columns]}, "B")
# #endregion
for column_name, column_type in required_columns:
    exists_before = column_exists('companies', column_name)
    # #region agent log
    debug_log("main.py:118", "Migration check before add", {"column": column_name, "exists": exists_before}, "B")
    # #endregion
    if not exists_before:
        try:
            # #region agent log
            debug_log("main.py:88", "Adding missing column", {"column": column_name, "type": column_type}, "B")
            # #endregion
            conn.execute(f"ALTER TABLE companies ADD COLUMN {column_name} {column_type}")
            conn.commit()
            # #region agent log
            debug_log("main.py:88", "Column added successfully", {"column": column_name}, "B")
            # #endregion
        except Exception as e:
            # #region agent log
            debug_log("main.py:88", "Failed to add column", {"column": column_name, "error": str(e), "error_type": type(e).__name__}, "B")
            # #endregion
            # Re-raise if it's not a "column already exists" error
            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                print(f"Warning: Failed to add column {column_name}: {e}")

# VC database schema
conn.execute("""
    CREATE TABLE IF NOT EXISTS vcs (
        id INTEGER PRIMARY KEY,
        firm_name TEXT UNIQUE,
        url TEXT,
        domain TEXT,
        type TEXT,
        stage TEXT,
        focus_areas TEXT,
        portfolio_url TEXT,
        discovered_from TEXT,
        user_added BOOLEAN DEFAULT 0,
        verified BOOLEAN DEFAULT 0,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
""")

def load_initial_vcs():
    """Load initial VCs from seed_data.json"""
    # Try multiple possible paths
    possible_paths = [
        Path(__file__).parent.parent / "data" / "seed_data.json",  # Absolute from this file (preferred)
        Path("data/seed_data.json"),  # From project root
        Path("../data/seed_data.json"),  # From backend directory
    ]
    
    seed_file = None
    for path in possible_paths:
        if path.exists():
            seed_file = path
            break
    
    if not seed_file:
        print(f"Seed data file not found. Tried: {[str(p) for p in possible_paths]}")
        return
    
    try:
        with open(seed_file, 'r') as f:
            seed_data = json.load(f)
        
        vcs = seed_data.get('vcs', [])
        for vc in vcs:
            # Check if VC already exists
            existing = conn.execute(
                "SELECT id FROM vcs WHERE firm_name = ?",
                (vc['firm_name'],)
            ).fetchone()
            
            if not existing:
                # Extract domain from URL
                url = vc.get('url', '')
                domain = ''
                if url:
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc.replace('www.', '')
                    except:
                        pass
                
                # Get portfolio URL (use url if portfolio_url not specified)
                portfolio_url = vc.get('portfolio_url_pattern') or vc.get('url', '')
                
                # Parse focus areas (empty for now, can be enhanced)
                focus_areas = []
                
                # Generate ID from firm_name hash
                vc_id = abs(hash(vc['firm_name'])) % 1000000
                
                conn.execute("""
                    INSERT INTO vcs 
                    (id, firm_name, url, domain, type, stage, focus_areas, portfolio_url, user_added, verified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vc_id,
                    vc['firm_name'],
                    url,
                    domain,
                    vc.get('type', 'VC'),
                    vc.get('stage', 'Unknown'),
                    json.dumps(focus_areas),
                    portfolio_url,
                    False,
                    False,
                    datetime.now(),
                    datetime.now()
                ))
        conn.commit()
        print(f"Loaded {len(vcs)} VCs from seed data")
    except Exception as e:
        print(f"Error loading initial VCs: {e}")

# Load mock data on startup (only if database is empty)
@app.on_event("startup")
async def startup_event():
    # #region agent log
    debug_log("main.py:255", "Startup event triggered", {"thread_id": threading.current_thread().ident}, "B")
    # #endregion
    # Ensure all required columns exist (re-run migration on startup)
    # #region agent log
    debug_log("main.py:255", "Re-running column migration on startup", {"thread_id": threading.current_thread().ident}, "B")
    # #endregion
    for column_name, column_type in required_columns:
        exists_before = column_exists('companies', column_name)
        # #region agent log
        debug_log("main.py:255", "Startup migration check", {"column": column_name, "exists": exists_before}, "B")
        # #endregion
        if not exists_before:
            try:
                # #region agent log
                debug_log("main.py:255", "Startup: Adding missing column", {"column": column_name, "type": column_type}, "B")
                # #endregion
                conn.execute(f"ALTER TABLE companies ADD COLUMN {column_name} {column_type}")
                conn.commit()
                # #region agent log
                debug_log("main.py:255", "Startup: Column added successfully", {"column": column_name}, "B")
                # #endregion
            except Exception as e:
                # #region agent log
                debug_log("main.py:255", "Startup: Failed to add column", {"column": column_name, "error": str(e), "error_type": type(e).__name__}, "B")
                # #endregion
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    print(f"Warning: Failed to add column {column_name}: {e}")
    
    # Check if database has any companies
    existing_count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    
    # Only load mock data if database is empty
    if existing_count == 0:
        mock_companies = load_mock_data()
        for company in mock_companies:
            # Check if company exists
            existing = conn.execute(
                "SELECT id FROM companies WHERE id = ?",
                (company['id'],)
            ).fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE companies SET
                    name = ?, domain = ?, yc_batch = ?, source = ?,
                    messaging_score = ?, motion_score = ?, market_score = ?,
                    stall_probability = ?, signals = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    company['name'],
                    company['domain'],
                    company.get('yc_batch', ''),
                    company.get('source', 'mock'),
                    company['messaging_score'],
                    company['motion_score'],
                    company['market_score'],
                    company['stall_probability'],
                    json.dumps(company.get('signals', {})),
                    datetime.now(),
                    company['id']
                ))
            else:
                conn.execute("""
                    INSERT INTO companies 
                    (id, name, domain, yc_batch, source, messaging_score, motion_score, market_score, stall_probability, signals, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company['id'],
                    company['name'],
                    company['domain'],
                    company.get('yc_batch', ''),
                    company.get('source', 'mock'),
                    company['messaging_score'],
                    company['motion_score'],
                    company['market_score'],
                    company['stall_probability'],
                    json.dumps(company.get('signals', {})),
                    datetime.now(),
                    datetime.now()
                ))
        conn.commit()
    
    # Load initial VCs from seed data
    load_initial_vcs()

class ScanRequest(BaseModel):
    url: str

class CompanyResponse(BaseModel):
    id: int
    name: str
    domain: str
    yc_batch: Optional[str]
    source: str
    messaging_score: float
    motion_score: float
    market_score: float
    stall_probability: str
    signals: dict
    funding_amount: Optional[float] = None
    funding_currency: Optional[str] = None
    employee_count: Optional[int] = None
    last_raise_date: Optional[str] = None
    last_raise_stage: Optional[str] = None
    fund_tier: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    created_at: str
    updated_at: str

class StatsResponse(BaseModel):
    total_companies: int
    avg_messaging_score: float
    avg_motion_score: float
    avg_market_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int

class PortfolioScrapeRequest(BaseModel):
    portfolio_names: List[str]

class PortfolioInfo(BaseModel):
    firm_name: str
    url: str
    domain: Optional[str] = None
    type: str
    stage: str
    focus_areas: Optional[List[str]] = []
    portfolio_url: Optional[str] = None
    user_added: bool = False
    verified: bool = False

class AddVCRequest(BaseModel):
    firm_name: str
    url: str
    portfolio_url: Optional[str] = None
    type: Optional[str] = "VC"
    stage: Optional[str] = None
    focus_areas: Optional[List[str]] = []

@app.get("/")
async def root():
    return {"message": "Celerio Scout API", "version": "1.0.0"}

@app.get("/companies", response_model=List[CompanyResponse])
async def get_companies(
    yc_batch: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    vector: Optional[str] = None,
    exclude_mock: Optional[bool] = False
):
    """Get all companies with optional filters"""
    # #region agent log
    debug_log("main.py:278", "get_companies entry", {"thread_id": threading.current_thread().ident, "params": {"yc_batch": yc_batch, "source": source}}, "A")
    # #endregion
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    
    if yc_batch:
        query += " AND yc_batch = ?"
        params.append(yc_batch)
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if exclude_mock:
        # Exclude mock data - mock companies have source='yc', 'antler', 'github', or 'mock'
        # Only show companies that were actually scanned (source='scanned')
        query += " AND source = 'scanned'"
    
    query += " ORDER BY (messaging_score + motion_score + market_score) / 3 DESC"
    
    # #region agent log
    debug_log("main.py:305", "Before conn.execute", {"thread_id": threading.current_thread().ident, "query": query[:100]}, "A")
    try:
    # #endregion
        results = conn.execute(query, params).fetchall()
    # #region agent log
    except Exception as db_err:
        debug_log("main.py:305", "conn.execute error", {"thread_id": threading.current_thread().ident, "error": str(db_err), "error_type": type(db_err).__name__}, "A")
        raise
    debug_log("main.py:305", "After conn.execute", {"thread_id": threading.current_thread().ident, "result_count": len(results)}, "A")
    # #endregion
    columns = [desc[0] for desc in conn.description]
    
    companies = []
    for row in results:
        company_dict = dict(zip(columns, row))
        # Parse JSON signals
        # #region agent log
        signals_raw = company_dict.get('signals')
        debug_log("main.py:312", "Before JSON parse signals", {"thread_id": threading.current_thread().ident, "signals_type": type(signals_raw).__name__, "is_empty_str": signals_raw == ""}, "D")
        # #endregion
        if isinstance(company_dict.get('signals'), str):
            try:
                company_dict['signals'] = json.loads(company_dict['signals'])
            # #region agent log
            except Exception as json_err:
                debug_log("main.py:313", "JSON parse signals error", {"thread_id": threading.current_thread().ident, "error": str(json_err), "signals_value": str(signals_raw)[:100]}, "D")
                company_dict['signals'] = {}
            # #endregion
        
        # Filter by vector if specified
        if vector:
            if vector == "messaging" and company_dict['messaging_score'] < (min_score or 50):
                continue
            elif vector == "motion" and company_dict['motion_score'] < (min_score or 50):
                continue
            elif vector == "market" and company_dict['market_score'] < (min_score or 50):
                continue
        
        # Parse focus areas
        if isinstance(company_dict.get('focus_areas'), str):
            try:
                company_dict['focus_areas'] = json.loads(company_dict['focus_areas'])
            except:
                company_dict['focus_areas'] = []
        
        # Format timestamps
        if company_dict.get('created_at'):
            company_dict['created_at'] = str(company_dict['created_at'])
        if company_dict.get('updated_at'):
            company_dict['updated_at'] = str(company_dict['updated_at'])
        
        # Format dates
        # #region agent log
        debug_log("main.py:338", "Before date conversion", {"thread_id": threading.current_thread().ident, "last_raise_date": str(company_dict.get('last_raise_date')), "is_none": company_dict.get('last_raise_date') is None}, "C")
        # #endregion
        if company_dict.get('last_raise_date'):
            try:
                company_dict['last_raise_date'] = str(company_dict['last_raise_date'])
            # #region agent log
            except Exception as date_err:
                debug_log("main.py:339", "Date conversion error", {"thread_id": threading.current_thread().ident, "error": str(date_err), "value": str(company_dict.get('last_raise_date'))}, "C")
                company_dict['last_raise_date'] = None
            # #endregion
        
        # Convert funding to millions for display
        if company_dict.get('funding_amount'):
            company_dict['funding_amount'] = company_dict['funding_amount'] / 1000000
        
        companies.append(CompanyResponse(**company_dict))
    
    return companies

class AdvancedSearchRequest(BaseModel):
    stages: Optional[List[str]] = None  # e.g., ["Seed", "Series A"]
    focus_areas: Optional[List[str]] = None  # e.g., ["AI/ML", "B2B SaaS"]
    funding_min: Optional[float] = None  # in millions USD
    funding_max: Optional[float] = None  # in millions USD
    employees_min: Optional[int] = None
    employees_max: Optional[int] = None
    months_post_raise_min: Optional[int] = None  # e.g., 12
    months_post_raise_max: Optional[int] = None  # e.g., 18
    fund_tiers: Optional[List[str]] = None  # e.g., ["Tier 1", "Tier 2"]
    rank_by_stall: Optional[bool] = True  # Rank by stall indicators
    free_text_query: Optional[str] = None  # Natural language query

class FreeTextSearchRequest(BaseModel):
    query: str  # Natural language search query
    session_id: Optional[str] = None  # Session ID for observability

@app.post("/companies/search", response_model=List[CompanyResponse])
async def advanced_search(request: AdvancedSearchRequest):
    # #region agent log
    debug_log("main.py:365", "advanced_search entry", {"thread_id": threading.current_thread().ident, "has_free_text": bool(request.free_text_query)}, "A")
    # #endregion
    """
    Advanced search for companies matching specific criteria:
    - Stage (Seed/Series A)
    - Focus areas (AI/B2B)
    - Funding amount ($3-15M)
    - Employee count (10-80)
    - Time post-raise (12-18 months)
    - Fund tier (Tier 1/2)
    - Ranked by stall indicators
    - Free text natural language query (parsed using Ollama)
    """
    # If free_text_query is provided, parse it first
    if request.free_text_query:
        try:
            from nlp_query_parser import parse_natural_language_query
            parsed = parse_natural_language_query(request.free_text_query)
            
            # Merge parsed params with explicit params (explicit takes precedence)
            if parsed.get('stages') and not request.stages:
                request.stages = parsed['stages']
            if parsed.get('focus_areas') and not request.focus_areas:
                request.focus_areas = parsed['focus_areas']
            if parsed.get('funding_min') is not None and request.funding_min is None:
                request.funding_min = parsed['funding_min']
            if parsed.get('funding_max') is not None and request.funding_max is None:
                request.funding_max = parsed['funding_max']
            if parsed.get('employees_min') is not None and request.employees_min is None:
                request.employees_min = parsed['employees_min']
            if parsed.get('employees_max') is not None and request.employees_max is None:
                request.employees_max = parsed['employees_max']
            if parsed.get('months_post_raise_min') is not None and request.months_post_raise_min is None:
                request.months_post_raise_min = parsed['months_post_raise_min']
            if parsed.get('months_post_raise_max') is not None and request.months_post_raise_max is None:
                request.months_post_raise_max = parsed['months_post_raise_max']
            if parsed.get('fund_tiers') and not request.fund_tiers:
                request.fund_tiers = parsed['fund_tiers']
            if 'rank_by_stall' in parsed:
                request.rank_by_stall = parsed['rank_by_stall']
        except Exception as e:
            print(f"Error parsing free text query: {e}")
    
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    filters_applied = False  # Track if any filters were applied
    
    # Ensure required columns exist before building query
    for col_name, col_type in required_columns:
        if not column_exists('companies', col_name):
            try:
                conn.execute(f"ALTER TABLE companies ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"Warning: Could not ensure column {col_name} exists: {e}")
    
    # Filter by stage
    if request.stages:
        # #region agent log
        debug_log("main.py:571", "Checking last_raise_stage before filter", {"thread_id": threading.current_thread().ident, "stages": request.stages}, "B")
        # #endregion
        try:
            stage_col_exists = column_exists('companies', 'last_raise_stage')
            # #region agent log
            debug_log("main.py:571", "last_raise_stage exists check result", {"thread_id": threading.current_thread().ident, "exists": stage_col_exists}, "B")
            # #endregion
            if stage_col_exists:
                placeholders = ','.join(['?' for _ in request.stages])
                # Use COALESCE to handle NULL values safely
                query += f" AND (COALESCE(last_raise_stage, '') IN ({placeholders}) OR yc_batch IS NOT NULL)"
                params.extend(request.stages)
                filters_applied = True
                # #region agent log
                debug_log("main.py:571", "Using last_raise_stage in query", {"thread_id": threading.current_thread().ident}, "B")
                # #endregion
            else:
                # Fallback: only filter by yc_batch if last_raise_stage column doesn't exist
                # #region agent log
                debug_log("main.py:571", "last_raise_stage column missing, skipping stage filter", {"thread_id": threading.current_thread().ident}, "B")
                # #endregion
                # Don't add stage filter if column doesn't exist - just continue without it
                pass
        except Exception as col_check_err:
            # #region agent log
            debug_log("main.py:571", "Error checking last_raise_stage, skipping filter", {"thread_id": threading.current_thread().ident, "error": str(col_check_err)[:100]}, "B")
            # #endregion
            # Safe fallback if column check fails - skip stage filter entirely
            pass  # Don't add any stage filter if column check fails
    
    # Filter by focus areas
    if request.focus_areas:
        # #region agent log
        debug_log("main.py:601", "Checking focus_areas before filter", {"thread_id": threading.current_thread().ident, "focus_areas": request.focus_areas}, "B")
        # #endregion
        try:
            focus_col_exists = column_exists('companies', 'focus_areas')
            # #region agent log
            debug_log("main.py:601", "focus_areas exists check result", {"thread_id": threading.current_thread().ident, "exists": focus_col_exists}, "B")
            # #endregion
            if focus_col_exists:
                focus_conditions = []
                for focus in request.focus_areas:
                    focus_conditions.append("COALESCE(focus_areas, '') LIKE ?")
                    params.append(f"%{focus}%")
                if focus_conditions:
                    query += " AND (" + " OR ".join(focus_conditions) + ")"
                    filters_applied = True
                # #region agent log
                debug_log("main.py:601", "Using focus_areas in query", {"thread_id": threading.current_thread().ident}, "B")
                # #endregion
            else:
                # #region agent log
                debug_log("main.py:601", "focus_areas column missing, skipping filter", {"thread_id": threading.current_thread().ident}, "B")
                # #endregion
                # Skip focus_areas filter if column doesn't exist
                pass
        except Exception as col_check_err:
            # #region agent log
            debug_log("main.py:601", "Error checking focus_areas, skipping filter", {"thread_id": threading.current_thread().ident, "error": str(col_check_err)[:100]}, "B")
            # #endregion
            # Safe fallback if column check fails - skip the filter
            pass
    
    # Filter by funding amount (convert to USD if needed)
    # IMPORTANT: Remove "OR ... IS NULL" to only match companies that actually have funding data
    if request.funding_min is not None and column_exists('companies', 'funding_amount'):
        query += " AND funding_amount >= ?"
        params.append(request.funding_min * 1000000)  # Convert millions to dollars
        filters_applied = True
    
    if request.funding_max is not None and column_exists('companies', 'funding_amount'):
        query += " AND funding_amount <= ?"
        params.append(request.funding_max * 1000000)
        filters_applied = True
    
    # Filter by employee count
    # IMPORTANT: Remove "OR ... IS NULL" to only match companies that actually have employee data
    # Check both 'employee_count' and 'employees' column names
    employee_col = None
    if column_exists('companies', 'employee_count'):
        employee_col = 'employee_count'
    elif column_exists('companies', 'employees'):
        employee_col = 'employees'
    
    if employee_col:
        if request.employees_min is not None:
            query += f" AND {employee_col} >= ?"
            params.append(request.employees_min)
            filters_applied = True
        
        if request.employees_max is not None:
            query += f" AND {employee_col} <= ?"
            params.append(request.employees_max)
            filters_applied = True
    
    # Filter by months post-raise
    # IMPORTANT: Remove "OR ... IS NULL" to only match companies that actually have raise dates
    if column_exists('companies', 'last_raise_date'):
        if request.months_post_raise_min is not None or request.months_post_raise_max is not None:
            if request.months_post_raise_min is not None:
                max_date = datetime.now() - timedelta(days=request.months_post_raise_min * 30)
                query += " AND last_raise_date <= ?"
                params.append(max_date.date())
                filters_applied = True
            
            if request.months_post_raise_max is not None:
                min_date = datetime.now() - timedelta(days=request.months_post_raise_max * 30)
                query += " AND last_raise_date >= ?"
                params.append(min_date.date())
                filters_applied = True
    
    # Filter by fund tier
    # IMPORTANT: Remove "OR ... IS NULL" to only match companies that actually have fund tier data
    if request.fund_tiers and column_exists('companies', 'fund_tier'):
        placeholders = ','.join(['?' for _ in request.fund_tiers])
        query += f" AND fund_tier IN ({placeholders})"
        params.extend(request.fund_tiers)
        filters_applied = True
    
    # Debug: Print what filters were requested
    print(f"[ADVANCED-SEARCH] Request filters:")
    print(f"  stages: {request.stages}")
    print(f"  focus_areas: {request.focus_areas}")
    print(f"  funding_min: {request.funding_min}, funding_max: {request.funding_max}")
    print(f"  employees_min: {request.employees_min}, employees_max: {request.employees_max}")
    print(f"  months_post_raise_min: {request.months_post_raise_min}, months_post_raise_max: {request.months_post_raise_max}")
    print(f"  fund_tiers: {request.fund_tiers}")
    print(f"[ADVANCED-SEARCH] filters_applied: {filters_applied}")
    print(f"[ADVANCED-SEARCH] Final query: {query[:500]}")
    print(f"[ADVANCED-SEARCH] Query params: {params}")
    
    # If no filters were applied, return empty result (don't return all companies)
    if not filters_applied:
        print(f"[ADVANCED-SEARCH] WARNING: No filters applied, returning empty result to prevent returning all companies")
        print(f"[ADVANCED-SEARCH] Request had: stages={request.stages}, focus_areas={request.focus_areas}, funding={request.funding_min}-{request.funding_max}, employees={request.employees_min}-{request.employees_max}")
        print(f"[ADVANCED-SEARCH] This means none of the requested filters matched existing columns or had valid values")
        return []
    
    # Export query details for debugging
    print(f"[ADVANCED-SEARCH] Executing query: {query[:300]}...")
    print(f"[ADVANCED-SEARCH] With {len(params)} parameters: {params[:5]}...")
    
    # Rank by stall indicators (lower scores = more stalling)
    if request.rank_by_stall:
        query += """ ORDER BY 
            (messaging_score + motion_score + market_score) / 3 ASC,
            CASE stall_probability 
                WHEN 'high' THEN 1 
                WHEN 'medium' THEN 2 
                WHEN 'low' THEN 3 
                ELSE 4 
            END ASC"""
    else:
        query += " ORDER BY (messaging_score + motion_score + market_score) / 3 DESC"
    
    # #region agent log
    debug_log("main.py:680", "Before advanced_search conn.execute", {"thread_id": threading.current_thread().ident, "query": query[:200]}, "A")
    try:
    # #endregion
        results = conn.execute(query, params).fetchall()
    # #region agent log
    except Exception as db_err:
        error_str = str(db_err)
        debug_log("main.py:680", "advanced_search conn.execute error", {"thread_id": threading.current_thread().ident, "error": error_str[:200], "error_type": type(db_err).__name__}, "A")
        # Check if error is about missing columns - if so, rebuild query without those columns
        # DuckDB error format: "Binder Error: Referenced column \"column_name\" not found in FROM clause!"
        if ("not found in FROM clause" in error_str or 
            "Binder Error" in error_str or 
            "Referenced column" in error_str or
            "not found" in error_str):
            # #region agent log
            debug_log("main.py:680", "Detected missing column error, rebuilding query without problematic columns", {"thread_id": threading.current_thread().ident}, "B")
            # #endregion
            # Extract column name from error if possible
            import re
            col_match = re.search(r'column "([^"]+)"', error_str)
            missing_col = col_match.group(1) if col_match else "unknown"
            print(f"[ADVANCED-SEARCH] WARNING: Column '{missing_col}' not found. Attempting to add it...")
            
            # Try to add ALL missing columns (not just the one that failed)
            # This handles the case where multiple columns are missing
            columns_to_add = {
                'last_raise_stage': 'TEXT',
                'focus_areas': 'TEXT',
                'funding_amount': 'REAL',
                'employee_count': 'INTEGER',
                'last_raise_date': 'DATE',
                'fund_tier': 'TEXT',
                'funding_currency': 'TEXT'
            }
            
            added_any = False
            for col_name, col_type in columns_to_add.items():
                try:
                    # Check if it exists first
                    if not column_exists('companies', col_name):
                        conn.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
                        conn.commit()
                        print(f"[ADVANCED-SEARCH] Added missing column '{col_name}'")
                        added_any = True
                except Exception as add_err:
                    if "already exists" not in str(add_err).lower():
                        print(f"[ADVANCED-SEARCH] Could not add column '{col_name}': {add_err}")
            
            if added_any:
                print(f"[ADVANCED-SEARCH] Retrying query after adding columns...")
                # Retry the original query
                try:
                    results = conn.execute(query, params).fetchall()
                    # #region agent log
                    debug_log("main.py:680", "Query succeeded after adding columns", {"thread_id": threading.current_thread().ident, "result_count": len(results)}, "B")
                    # #endregion
                except Exception as retry_err:
                    # Still failing - rebuild query without problematic filters
                    print(f"[ADVANCED-SEARCH] Query still failing after adding columns: {retry_err}")
                    # Build minimal query with only basic filters
                    query_safe = "SELECT * FROM companies WHERE 1=1"
                    params_safe = []
                    # Only add filters for columns we're 100% sure exist
                    # Skip stage, focus_areas, funding, employees, dates, fund_tier filters
                    query_safe += " ORDER BY (messaging_score + motion_score + market_score) / 3 DESC LIMIT 100"
                    results = conn.execute(query_safe, params_safe).fetchall()
                    print(f"[ADVANCED-SEARCH] Using minimal query, found {len(results)} companies")
            else:
                # No columns were added (they might all exist but connection cache is stale)
                # Rebuild query without problematic columns
                print(f"[ADVANCED-SEARCH] Columns appear to exist but connection cache is stale. Building safe query...")
                query_safe = "SELECT * FROM companies WHERE 1=1"
                params_safe = []
                # Only use filters for columns that definitely exist (from CREATE TABLE)
                # Skip: last_raise_stage, focus_areas, funding_amount, employee_count, last_raise_date, fund_tier
                query_safe += " ORDER BY (messaging_score + motion_score + market_score) / 3 DESC LIMIT 100"
                results = conn.execute(query_safe, params_safe).fetchall()
                print(f"[ADVANCED-SEARCH] Using safe query without new columns, found {len(results)} companies")
        else:
            raise
    debug_log("main.py:680", "After advanced_search conn.execute", {"thread_id": threading.current_thread().ident, "result_count": len(results)}, "A")
    # #endregion
    columns = [desc[0] for desc in conn.description]
    
    companies = []
    for row in results:
        company_dict = dict(zip(columns, row))
        
        # Parse JSON fields
        # #region agent log
        signals_raw = company_dict.get('signals')
        debug_log("main.py:483", "Before advanced search JSON parse", {"thread_id": threading.current_thread().ident, "signals_type": type(signals_raw).__name__, "is_empty_str": signals_raw == ""}, "D")
        # #endregion
        if isinstance(company_dict.get('signals'), str):
            try:
                company_dict['signals'] = json.loads(company_dict['signals'])
            # #region agent log
            except Exception as json_err:
                debug_log("main.py:484", "Advanced search JSON parse signals error", {"thread_id": threading.current_thread().ident, "error": str(json_err), "signals_value": str(signals_raw)[:100]}, "D")
                company_dict['signals'] = {}
            # #endregion
        
        if isinstance(company_dict.get('focus_areas'), str):
            try:
                company_dict['focus_areas'] = json.loads(company_dict['focus_areas'])
            # #region agent log
            except Exception as json_err:
                debug_log("main.py:488", "Advanced search JSON parse focus_areas error", {"thread_id": threading.current_thread().ident, "error": str(json_err)}, "D")
                company_dict['focus_areas'] = []
            # #endregion
        
        # Format timestamps and dates
        # #region agent log
        debug_log("main.py:493", "Before advanced search date conversion", {"thread_id": threading.current_thread().ident, "last_raise_date": str(company_dict.get('last_raise_date')), "is_none": company_dict.get('last_raise_date') is None}, "C")
        # #endregion
        if company_dict.get('created_at'):
            company_dict['created_at'] = str(company_dict['created_at'])
        if company_dict.get('updated_at'):
            company_dict['updated_at'] = str(company_dict['updated_at'])
        if company_dict.get('last_raise_date'):
            try:
                company_dict['last_raise_date'] = str(company_dict['last_raise_date'])
            # #region agent log
            except Exception as date_err:
                debug_log("main.py:498", "Advanced search date conversion error", {"thread_id": threading.current_thread().ident, "error": str(date_err), "value": str(company_dict.get('last_raise_date'))}, "C")
                company_dict['last_raise_date'] = None
            # #endregion
        
        # Convert funding to millions for display
        if company_dict.get('funding_amount'):
            company_dict['funding_amount'] = company_dict['funding_amount'] / 1000000
        
        companies.append(CompanyResponse(**company_dict))
    
    return companies

@app.post("/companies/search/free-text")
async def free_text_search(request: FreeTextSearchRequest):
    """
    Free text natural language search endpoint.
    Parses the query using Ollama, discovers companies from web sources,
    and returns matching companies.
    """
    try:
        from nlp_query_parser import parse_natural_language_query
        from web_company_discovery import WebCompanyDiscovery
        
        print(f"[FREE-TEXT] ===== STARTING FREE-TEXT SEARCH =====")
        print(f"[FREE-TEXT] Received query: {request.query}, Session ID: {request.session_id}")
        
        # Generate session ID if not provided
        session_id = request.session_id or f"scrape-{int(datetime.now().timestamp() * 1000)}"
        print(f"[FREE-TEXT] Using session ID: {session_id}")
        
        # Validate query is not empty
        if not request.query or not request.query.strip():
            print(f"[FREE-TEXT] ERROR: Empty query received")
            raise HTTPException(status_code=400, detail="Query cannot be empty. Please provide a search query.")
        
        # Set up progress callback for portfolio scraping observability
        progress_callback = None
        if session_id:
            try:
                from portfolio_scraping_monitor import get_progress_callback
                progress_callback = get_progress_callback(session_id)
                print(f"[FREE-TEXT] Initialized progress callback for session: {session_id}")
                # Emit initial event
                progress_callback({
                    'type': 'query_received',
                    'query': request.query,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"[FREE-TEXT] Warning: Could not initialize progress callback: {e}")
        
        # Parse the natural language query
        if progress_callback:
            progress_callback({
                'type': 'parsing_started',
                'message': 'Parsing natural language query...',
                'timestamp': datetime.now().isoformat()
            })
        
        parsed_params = parse_natural_language_query(request.query, progress_callback=progress_callback)
        
        if progress_callback:
            progress_callback({
                'type': 'parsing_complete',
                'parsed_params': parsed_params,
                'message': f'Query parsed: {json.dumps(parsed_params, indent=2)}',
                'timestamp': datetime.now().isoformat()
            })
        
        # Check if this is a portfolio query (special handling)
        if parsed_params.get('is_portfolio_query'):
            print(f"[FREE-TEXT] Detected portfolio query - will scrape portfolios directly")
            if progress_callback:
                progress_callback({
                    'type': 'portfolio_query_detected',
                    'sources': parsed_params.get('portfolio_sources', []),
                    'message': f"Portfolio query detected for sources: {parsed_params.get('portfolio_sources', [])}",
                    'timestamp': datetime.now().isoformat()
                })
            # Portfolio queries bypass normal filtering - return companies directly after scraping
            # Continue to web discovery which will handle portfolio scraping
        else:
            # Validate that at least some criteria were extracted
            has_criteria = any([
                parsed_params.get('stages'),
                parsed_params.get('focus_areas'),
                parsed_params.get('funding_min') is not None,
                parsed_params.get('funding_max') is not None,
                parsed_params.get('employees_min') is not None,
                parsed_params.get('employees_max') is not None,
                parsed_params.get('months_post_raise_min') is not None,
                parsed_params.get('months_post_raise_max') is not None,
                parsed_params.get('fund_tiers'),
                parsed_params.get('keywords')
            ])
            
            if not has_criteria:
                print(f"[FREE-TEXT] WARNING: No search criteria extracted from query: '{request.query}'")
                print(f"[FREE-TEXT] Parsed params were: {parsed_params}")
                # Return empty result for queries that don't match any known patterns
                return []
        print(f"[FREE-TEXT] Parsed parameters: {json.dumps(parsed_params, indent=2)}")
        print(f"[FREE-TEXT] Extracted stages: {parsed_params.get('stages')}")
        print(f"[FREE-TEXT] Extracted focus_areas: {parsed_params.get('focus_areas')}")
        print(f"[FREE-TEXT] Extracted funding range: ${parsed_params.get('funding_min')}M - ${parsed_params.get('funding_max')}M")
        print(f"[FREE-TEXT] Extracted employee range: {parsed_params.get('employees_min')} - {parsed_params.get('employees_max')}")
        
        # Discover companies from web sources based on parsed criteria
        print(f"[FREE-TEXT] Starting web discovery with criteria: {json.dumps(parsed_params, indent=2)}")
        if progress_callback:
            progress_callback({
                'type': 'web_discovery_started',
                'message': 'Starting web discovery...',
                'criteria': parsed_params,
                'timestamp': datetime.now().isoformat()
            })
        discovery = WebCompanyDiscovery(progress_callback=progress_callback)
        discovered_count = 0
        discovered_companies = []
        try:
            # For portfolio queries, start scraping in background and return immediately
            if parsed_params.get('is_portfolio_query'):
                print(f"[FREE-TEXT] Portfolio query - starting background scraping task")
                # Start scraping in background task
                import asyncio
                async def background_scrape():
                    try:
                        if progress_callback:
                            progress_callback({
                                'type': 'scraping_initiated',
                                'message': 'Background scraping task started',
                                'sources': parsed_params.get('portfolio_sources', []),
                                'timestamp': datetime.now().isoformat()
                            })
                        companies = await discovery.discover_companies(parsed_params, progress_callback=progress_callback)
                        print(f"[FREE-TEXT] Background scraping completed: {len(companies)} companies")
                        if progress_callback:
                            progress_callback({
                                'type': 'scraping_complete',
                                'companies_found': len(companies),
                                'message': f'Scraping completed: {len(companies)} companies found',
                                'timestamp': datetime.now().isoformat()
                            })
                    except Exception as e:
                        print(f"[FREE-TEXT] Background scraping error: {e}")
                        import traceback
                        traceback.print_exc()
                        if progress_callback:
                            progress_callback({
                                'type': 'error',
                                'message': f'Scraping error: {str(e)}',
                                'error': str(e),
                                'timestamp': datetime.now().isoformat()
                            })
                    finally:
                        try:
                            await discovery.close()
                        except:
                            pass
                
                # Start background task (don't await - let it run in background)
                asyncio.create_task(background_scrape())
                # Return empty list immediately - companies will be added to DB as scraping progresses
                discovered_companies = []
                
                # Return immediately for portfolio queries - don't wait for database query
                print(f"[FREE-TEXT] Portfolio query - returning immediately with session_id: {session_id}")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    content=[],
                    headers={"X-Session-ID": session_id}
                )
            else:
                # For non-portfolio queries, wait for results
                discovered_companies = await discovery.discover_companies(parsed_params, progress_callback=progress_callback)
                print(f"[FREE-TEXT] Discovered {len(discovered_companies)} companies from web sources")
            
            # Store discovered companies in database
            if discovered_companies:
                for company in discovered_companies:
                    try:
                        domain = company.get('domain', '').strip()
                        if not domain:
                            continue
                            
                        # Check if company already exists
                        existing = conn.execute(
                            "SELECT id FROM companies WHERE domain = ?",
                            (domain,)
                        ).fetchone()
                        
                        if not existing:
                            # Ensure columns exist before inserting
                            for col_name, col_type in required_columns:
                                if not column_exists('companies', col_name):
                                    try:
                                        conn.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
                                        conn.commit()
                                    except Exception as e:
                                        if "already exists" not in str(e).lower():
                                            print(f"[FREE-TEXT] Warning: Could not add column {col_name}: {e}")
                            
                            # Insert discovered company
                            company_id = abs(hash(domain)) % 1000000
                            conn.execute("""
                                INSERT INTO companies 
                                (id, name, domain, source, last_raise_stage, focus_areas, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                company_id,
                                company.get('name', ''),
                                domain,
                                company.get('source', 'web_discovery'),
                                company.get('last_raise_stage'),
                                json.dumps(company.get('focus_areas', [])),
                                datetime.now(),
                                datetime.now()
                            ))
                            conn.commit()
                            discovered_count += 1
                            print(f"[FREE-TEXT] ✓ Added discovered company: {company.get('name')} ({domain})")
                        else:
                            print(f"[FREE-TEXT] ⊗ Company already exists: {domain}")
                    except Exception as e:
                        print(f"[FREE-TEXT] Error storing discovered company {company.get('name', 'unknown')}: {e}")
                        import traceback
                        traceback.print_exc()
                        conn.rollback()
            
            print(f"[FREE-TEXT] Successfully stored {discovered_count} new companies from web discovery")
        except Exception as e:
            print(f"[FREE-TEXT] Error during web discovery: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Only close discovery if we didn't return early for portfolio queries
            # (discovery.close() will be called in background task for portfolio queries)
            if not parsed_params.get('is_portfolio_query'):
                await discovery.close()
        
        # If this was a portfolio query, we should have already returned above
        # Skip the rest of the function for portfolio queries
        if parsed_params.get('is_portfolio_query'):
            # This should never be reached, but just in case:
            print(f"[FREE-TEXT] WARNING: Portfolio query reached database query section - this shouldn't happen")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=[],
                headers={"X-Session-ID": session_id}
            )
        
        # Ensure required columns exist before building query
        # This MUST happen before calling advanced_search
        print(f"[FREE-TEXT] Ensuring required columns exist...")
        for col_name, col_type in required_columns:
            exists = column_exists('companies', col_name)
            print(f"[FREE-TEXT] Column '{col_name}' exists: {exists}")
            if not exists:
                try:
                    print(f"[FREE-TEXT] Adding missing column '{col_name}'...")
                    conn.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    # Verify it was added
                    exists_after = column_exists('companies', col_name)
                    print(f"[FREE-TEXT] Column '{col_name}' added successfully. Exists now: {exists_after}")
                    if not exists_after:
                        raise Exception(f"Failed to add column {col_name} - column_exists still returns False")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already exists" not in error_msg and "duplicate" not in error_msg:
                        print(f"[FREE-TEXT] ERROR: Could not ensure column {col_name} exists: {e}")
                        raise HTTPException(
                            status_code=500, 
                            detail=f"Database schema error: Could not add required column '{col_name}'. Please restart the backend server."
                        )
        
        print(f"[FREE-TEXT] All required columns verified. Proceeding with search...")
        
        # For portfolio queries, return discovered companies directly without filtering
        # NOTE: This should never be reached for portfolio queries (they return earlier)
        if parsed_params.get('is_portfolio_query'):
            print(f"[FREE-TEXT] Portfolio query detected - returning discovered companies directly")
            
            # Query database for companies that match portfolio sources
            # This allows polling to get companies as they're added
            portfolio_sources = parsed_params.get('portfolio_sources', [])
            db_query = "SELECT * FROM companies WHERE 1=1"
            db_params = []
            
            if 'yc' in portfolio_sources:
                db_query += " AND (source = 'yc' OR source = 'Y Combinator' OR yc_batch IS NOT NULL)"
            if 'antler' in portfolio_sources:
                db_query += " AND (source = 'antler' OR source = 'Antler')"
            
            # If both sources, use OR logic
            if 'yc' in portfolio_sources and 'antler' in portfolio_sources:
                db_query = "SELECT * FROM companies WHERE (source = 'yc' OR source = 'Y Combinator' OR yc_batch IS NOT NULL) OR (source = 'antler' OR source = 'Antler')"
            
            db_query += " ORDER BY created_at DESC LIMIT 10000"  # Limit to prevent huge results
            
            try:
                db_results = conn.execute(db_query, db_params).fetchall()
                db_columns = [desc[0] for desc in conn.description]
                print(f"[FREE-TEXT] Found {len(db_results)} companies in database matching portfolio sources")
                
                # Convert database results to CompanyResponse format
                for row in db_results:
                    company_dict = dict(zip(db_columns, row))
                    # Parse JSON fields
                    if isinstance(company_dict.get('signals'), str):
                        try:
                            company_dict['signals'] = json.loads(company_dict['signals'])
                        except:
                            company_dict['signals'] = {}
                    if isinstance(company_dict.get('focus_areas'), str):
                        try:
                            company_dict['focus_areas'] = json.loads(company_dict['focus_areas'])
                        except:
                            company_dict['focus_areas'] = []
                    # Format dates
                    if company_dict.get('created_at'):
                        company_dict['created_at'] = str(company_dict['created_at'])
                    if company_dict.get('updated_at'):
                        company_dict['updated_at'] = str(company_dict['updated_at'])
                    if company_dict.get('last_raise_date'):
                        company_dict['last_raise_date'] = str(company_dict['last_raise_date']) if company_dict.get('last_raise_date') else None
                    # Convert funding to millions
                    if company_dict.get('funding_amount'):
                        company_dict['funding_amount'] = company_dict['funding_amount'] / 1000000
                    
                    try:
                        company_responses.append(CompanyResponse(**company_dict))
                    except Exception as e:
                        print(f"[FREE-TEXT] Error converting DB company: {e}")
                        continue
            except Exception as e:
                print(f"[FREE-TEXT] Error querying database for portfolio companies: {e}")
                import traceback
                traceback.print_exc()
            
            # Also add any newly discovered companies that aren't in DB yet
            for company in discovered_companies:
                try:
                    # Ensure required fields exist
                    company_dict = {
                        'id': abs(hash(company.get('domain', company.get('name', '')))) % 1000000,
                        'name': company.get('name', ''),
                        'domain': company.get('domain', ''),
                        'source': company.get('source', 'web_discovery'),
                        'yc_batch': company.get('yc_batch', ''),
                        'focus_areas': json.dumps(company.get('focus_areas', [])),
                        'messaging_score': 0.0,
                        'motion_score': 0.0,
                        'market_score': 0.0,
                        'stall_probability': 'unknown',
                        'signals': json.dumps([]),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    company_responses.append(CompanyResponse(**company_dict))
                except Exception as e:
                    print(f"[FREE-TEXT] Error converting company {company.get('name')}: {e}")
                    continue
            
            print(f"[FREE-TEXT] Returning {len(company_responses)} portfolio companies (scraping may continue in background)")
            # Return with session_id in response headers for frontend to pick up
            # Note: For portfolio queries, scraping happens asynchronously
            # Companies will be added to database as scraping progresses
            # Frontend should use WebSocket monitor to see progress
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                content=[c.dict() for c in company_responses],
                headers={"X-Session-ID": session_id}
            )
            return response
        
        # Convert to AdvancedSearchRequest - use safe defaults for missing fields
        search_request = AdvancedSearchRequest(
            stages=parsed_params.get('stages'),
            focus_areas=parsed_params.get('focus_areas'),
            funding_min=parsed_params.get('funding_min'),
            funding_max=parsed_params.get('funding_max'),
            employees_min=parsed_params.get('employees_min'),
            employees_max=parsed_params.get('employees_max'),
            months_post_raise_min=parsed_params.get('months_post_raise_min'),
            months_post_raise_max=parsed_params.get('months_post_raise_max'),
            fund_tiers=parsed_params.get('fund_tiers'),
            rank_by_stall=parsed_params.get('rank_by_stall', False),
            free_text_query=None  # Already parsed
        )
        
        # Use the existing advanced_search logic
        results = await advanced_search(search_request)
        print(f"[FREE-TEXT] Returning {len(results)} companies")
        return results
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[FREE-TEXT] Error in free text search: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

@app.post("/scan", response_model=CompanyResponse)
async def scan_company_endpoint(request: ScanRequest):
    """Trigger a live scan for a specific URL"""
    # #region agent log
    debug_log("main.py:529", "scan_company_endpoint entry", {"thread_id": threading.current_thread().ident, "url": request.url}, "A")
    # #endregion
    try:
        result = await scan_company(request.url)
        
        # Store in database
        # #region agent log
        debug_log("main.py:536", "Before database check", {"thread_id": threading.current_thread().ident, "company_id": result['id']}, "A")
        # #endregion
        try:
            existing = conn.execute(
                "SELECT id FROM companies WHERE id = ?",
                (result['id'],)
            ).fetchone()
        # #region agent log
        except Exception as db_err:
            debug_log("main.py:536", "Database check error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
            raise
        # #endregion
        
        if existing:
            # #region agent log
            debug_log("main.py:542", "Before UPDATE", {"thread_id": threading.current_thread().ident}, "A")
            # #endregion
            try:
                conn.execute("""
                    UPDATE companies SET
                        name = ?, domain = ?, yc_batch = ?, source = ?,
                        messaging_score = ?, motion_score = ?, market_score = ?,
                        stall_probability = ?, signals = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    result['name'],
                    result['domain'],
                    result.get('yc_batch', ''),
                    'scanned',
                    result['messaging_score'],
                    result['motion_score'],
                    result['market_score'],
                    result['stall_probability'],
                    json.dumps(result.get('signals', {})),
                    datetime.now(),
                    result['id']
                ))
            # #region agent log
            except Exception as db_err:
                debug_log("main.py:542", "UPDATE error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
                raise
            # #endregion
        else:
            # #region agent log
            debug_log("main.py:562", "Before INSERT", {"thread_id": threading.current_thread().ident}, "A")
            # #endregion
            try:
                conn.execute("""
                    INSERT INTO companies 
                    (id, name, domain, yc_batch, source, messaging_score, motion_score, market_score, stall_probability, signals, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['id'],
                    result['name'],
                    result['domain'],
                    result.get('yc_batch', ''),
                    'scanned',
                    result['messaging_score'],
                    result['motion_score'],
                    result['market_score'],
                    result['stall_probability'],
                    json.dumps(result.get('signals', {})),
                    datetime.now(),
                    datetime.now()
                ))
            # #region agent log
            except Exception as db_err:
                debug_log("main.py:562", "INSERT error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
                raise
            # #endregion
        # #region agent log
        debug_log("main.py:580", "Before commit", {"thread_id": threading.current_thread().ident}, "A")
        # #endregion
        try:
            conn.commit()
        # #region agent log
        except Exception as db_err:
            debug_log("main.py:580", "Commit error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
            raise
        debug_log("main.py:580", "After commit", {"thread_id": threading.current_thread().ident}, "A")
        # #endregion
        
        return CompanyResponse(**result)
    except Exception as e:
        # #region agent log
        debug_log("main.py:583", "scan_company_endpoint exception", {"thread_id": threading.current_thread().ident, "error": str(e), "error_type": type(e).__name__}, "B")
        # #endregion
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get aggregate market health statistics"""
    results = conn.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(messaging_score) as avg_messaging,
            AVG(motion_score) as avg_motion,
            AVG(market_score) as avg_market,
            SUM(CASE WHEN stall_probability = 'high' THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN stall_probability = 'medium' THEN 1 ELSE 0 END) as medium_risk,
            SUM(CASE WHEN stall_probability = 'low' THEN 1 ELSE 0 END) as low_risk
        FROM companies
    """).fetchone()
    
    return StatsResponse(
        total_companies=results[0] or 0,
        avg_messaging_score=round(results[1] or 0, 2),
        avg_motion_score=round(results[2] or 0, 2),
        avg_market_score=round(results[3] or 0, 2),
        high_risk_count=results[4] or 0,
        medium_risk_count=results[5] or 0,
        low_risk_count=results[6] or 0
    )

@app.get("/portfolios", response_model=List[PortfolioInfo])
async def get_portfolios(
    stage: Optional[str] = None,
    focus_area: Optional[str] = None,
    vc_type: Optional[str] = None
):
    """Get list of available portfolios from database"""
    query = "SELECT * FROM vcs WHERE 1=1"
    params = []
    
    if stage:
        query += " AND stage = ?"
        params.append(stage)
    
    if vc_type:
        query += " AND type = ?"
        params.append(vc_type)
    
    if focus_area:
        query += " AND focus_areas LIKE ?"
        params.append(f"%{focus_area}%")
    
    query += " ORDER BY firm_name"
    
    results = conn.execute(query, params).fetchall()
    columns = [desc[0] for desc in conn.description]
    
    portfolios = []
    for row in results:
        vc_dict = dict(zip(columns, row))
        focus_areas = []
        if vc_dict.get('focus_areas'):
            try:
                focus_areas = json.loads(vc_dict['focus_areas'])
            except:
                focus_areas = [vc_dict['focus_areas']] if vc_dict['focus_areas'] else []
        
        portfolios.append(PortfolioInfo(
            firm_name=vc_dict['firm_name'],
            url=vc_dict['url'],
            domain=vc_dict.get('domain'),
            type=vc_dict.get('type', 'VC'),
            stage=vc_dict.get('stage', 'Unknown'),
            focus_areas=focus_areas,
            portfolio_url=vc_dict.get('portfolio_url'),
            user_added=bool(vc_dict.get('user_added', 0)),
            verified=bool(vc_dict.get('verified', 0))
        ))
    
    return portfolios

@app.post("/portfolios/load-seed")
async def load_seed_vcs():
    """Manually load VCs from seed_data.json"""
    try:
        load_initial_vcs()
        # Count VCs after loading
        count = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
        return {
            "message": "Seed VCs loaded successfully",
            "total_vcs": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolios/discover")
async def discover_vcs():
    """Discover new VCs from web sources"""
    discovery = VCDiscovery()
    discovered_vcs = await discovery.discover_all()
    
    added_count = 0
    for vc in discovered_vcs:
        try:
            # Check if VC already exists
            existing = conn.execute(
                "SELECT id FROM vcs WHERE firm_name = ?",
                (vc['firm_name'],)
            ).fetchone()
            
            if not existing:
                focus_areas_json = json.dumps(vc.get('focus_areas', []))
                vc_id = abs(hash(vc['firm_name'])) % 1000000
                conn.execute("""
                    INSERT INTO vcs 
                    (id, firm_name, url, domain, type, stage, focus_areas, discovered_from, user_added, verified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vc_id,
                    vc['firm_name'],
                    vc['url'],
                    vc.get('domain', ''),
                    vc.get('type', 'VC'),
                    vc.get('stage', 'Unknown'),
                    focus_areas_json,
                    vc.get('discovered_from', ''),
                    False,
                    False,
                    datetime.now(),
                    datetime.now()
                ))
                added_count += 1
        except Exception as e:
            print(f"Error adding VC {vc.get('firm_name')}: {e}")
            continue
    
    conn.commit()
    
    return {
        "discovered": len(discovered_vcs),
        "added": added_count,
        "message": f"Discovered {len(discovered_vcs)} VCs, added {added_count} new ones"
    }

@app.post("/portfolios/add", response_model=PortfolioInfo)
async def add_vc(request: AddVCRequest):
    """Add a custom VC portfolio"""
    # Extract domain from URL
    from urllib.parse import urlparse
    parsed = urlparse(request.url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Check if VC already exists
    existing = conn.execute(
        "SELECT id FROM vcs WHERE firm_name = ? OR domain = ?",
        (request.firm_name, domain)
    ).fetchone()
    
    if existing:
        raise HTTPException(status_code=400, detail="VC already exists")
    
    # Insert new VC
    focus_areas_json = json.dumps(request.focus_areas or [])
    portfolio_url = request.portfolio_url or request.url
    vc_id = abs(hash(request.firm_name)) % 1000000
    
    conn.execute("""
        INSERT INTO vcs 
        (id, firm_name, url, domain, type, stage, focus_areas, portfolio_url, user_added, verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vc_id,
        request.firm_name,
        request.url,
        domain,
        request.type or 'VC',
        request.stage or 'Unknown',
        focus_areas_json,
        portfolio_url,
        True,  # User added
        False,  # Not verified yet
        datetime.now(),
        datetime.now()
    ))
    conn.commit()
    
    return PortfolioInfo(
        firm_name=request.firm_name,
        url=request.url,
        domain=domain,
        type=request.type or 'VC',
        stage=request.stage or 'Unknown',
        focus_areas=request.focus_areas or [],
        portfolio_url=portfolio_url,
        user_added=True,
        verified=False
    )

@app.get("/portfolios/stages")
async def get_stages():
    """Get list of unique stages"""
    results = conn.execute("SELECT DISTINCT stage FROM vcs WHERE stage IS NOT NULL").fetchall()
    return [row[0] for row in results if row[0]]

@app.get("/portfolios/focus-areas")
async def get_focus_areas():
    """Get list of unique focus areas"""
    results = conn.execute("SELECT focus_areas FROM vcs WHERE focus_areas IS NOT NULL").fetchall()
    all_focus_areas = set()
    for row in results:
        try:
            focus_areas = json.loads(row[0])
            all_focus_areas.update(focus_areas)
        except:
            if row[0]:
                all_focus_areas.add(row[0])
    return sorted(list(all_focus_areas))

@app.post("/portfolios/scrape")
async def scrape_portfolios(request: PortfolioScrapeRequest):
    # #region agent log
    debug_log("main.py:801", "scrape_portfolios entry", {"thread_id": threading.current_thread().ident, "portfolio_count": len(request.portfolio_names)}, "E")
    # #endregion
    """
    Scrape selected portfolios and analyze companies
    Returns list of analyzed companies
    """
    import asyncio
    
    scraper = PortfolioScraper()
    
    # Get portfolio URLs from database
    placeholders = ','.join(['?' for _ in request.portfolio_names])
    vc_results = conn.execute(
        f"SELECT firm_name, portfolio_url, url, type FROM vcs WHERE firm_name IN ({placeholders})",
        request.portfolio_names
    ).fetchall()
    
    # Build portfolio dict for scraper
    portfolio_dict = {}
    for row in vc_results:
        firm_name = row[0]
        portfolio_url = row[1] or row[2]  # Use portfolio_url or fallback to url
        vc_type = row[3] or 'VC'
        portfolio_dict[firm_name] = {
            'url': portfolio_url,
            'type': vc_type
        }
    
    # Scrape portfolios with progress logging and timeout
    portfolio_results = {}
    scraped_count = 0
    
    try:
        for idx, firm_name in enumerate(request.portfolio_names):
            if firm_name in portfolio_dict:
                print(f"[{idx+1}/{len(request.portfolio_names)}] Scraping {firm_name}...")
                vc_info = portfolio_dict[firm_name]
                
                # Add timeout per portfolio (5 minutes max)
                try:
                    companies = await asyncio.wait_for(
                        scraper.scrape_portfolio(firm_name, vc_info['url'], vc_info['type']),
                        timeout=300.0  # 5 minutes per portfolio
                    )
                    portfolio_results[firm_name] = companies
                    scraped_count += len(companies)
                    print(f"Found {len(companies)} companies from {firm_name}")
                except asyncio.TimeoutError:
                    print(f"Timeout scraping {firm_name} - continuing with next portfolio")
                    portfolio_results[firm_name] = []
                except Exception as e:
                    print(f"Error scraping {firm_name}: {e}")
                    portfolio_results[firm_name] = []
    finally:
        # Clean up scraper session
        await scraper.close_session()
    
    all_companies = []
    analyzed_companies = []
    
    # Collect all companies from scraped portfolios
    for firm_name, companies in portfolio_results.items():
        all_companies.extend(companies)
    
    print(f"Total companies scraped: {len(all_companies)}")
    
    # Analyze each company (with rate limiting and progress)
    total_to_analyze = len(all_companies)
    analyzed_count = 0
    skipped_count = 0
    
    for idx, company in enumerate(all_companies):
        if idx % 10 == 0 and total_to_analyze > 10:
            print(f"Analyzing company {idx+1}/{total_to_analyze}...")
        try:
            # Get domain - must be present, skip if not available
            domain = company.get('domain', '').strip()
            if not domain:
                skipped_count += 1
                if skipped_count <= 5:  # Only log first few
                    print(f"Skipping {company.get('name', 'Unknown')} - no domain found")
                continue
            
            # Validate domain format
            if '.' not in domain or len(domain) < 4:
                skipped_count += 1
                if skipped_count <= 5:
                    print(f"Skipping {company.get('name', 'Unknown')} - invalid domain: {domain}")
                continue
            
            # Enrich company data with funding, employees, etc.
            enriched_company = await enrich_company_data(company, domain)
            
            # Calculate scores
            scores = await calculate_scores(domain, company['name'])
            
            # Create company record
            company_id = hash(domain) % 1000000
            now = datetime.now()
            
            # Parse focus areas
            focus_areas = enriched_company.get('focus_areas', [])
            if isinstance(focus_areas, str):
                try:
                    focus_areas = json.loads(focus_areas)
                except:
                    focus_areas = [focus_areas] if focus_areas else []
            
            company_record = {
                'id': company_id,
                'name': company['name'],
                'domain': domain,
                'yc_batch': company.get('yc_batch', ''),
                'source': company.get('source', 'portfolio'),
                'messaging_score': scores['messaging_score'],
                'motion_score': scores['motion_score'],
                'market_score': scores['market_score'],
                'stall_probability': scores['stall_probability'],
                'signals': scores['signals'],
                'funding_amount': enriched_company.get('funding_amount'),
                'funding_currency': enriched_company.get('funding_currency', 'USD'),
                'employee_count': enriched_company.get('employee_count'),
                'last_raise_date': enriched_company.get('last_raise_date'),
                'last_raise_stage': enriched_company.get('last_raise_stage'),
                'fund_tier': enriched_company.get('fund_tier'),
                'focus_areas': json.dumps(focus_areas),
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            # Store in database
            # #region agent log
            debug_log("main.py:932", "Before portfolio scrape DB check", {"thread_id": threading.current_thread().ident, "company_id": company_id, "company_name": company_record['name']}, "E")
            # #endregion
            try:
                existing = conn.execute(
                    "SELECT id FROM companies WHERE id = ?",
                    (company_id,)
                ).fetchone()
            # #region agent log
            except Exception as db_err:
                debug_log("main.py:932", "Portfolio scrape DB check error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
                raise
            # #endregion
            
            if existing:
                # #region agent log
                debug_log("main.py:938", "Before portfolio scrape UPDATE", {"thread_id": threading.current_thread().ident}, "E")
                # #endregion
                try:
                    conn.execute("""
                        UPDATE companies SET
                            name = ?, domain = ?, yc_batch = ?, source = ?,
                            messaging_score = ?, motion_score = ?, market_score = ?,
                            stall_probability = ?, signals = ?, 
                            funding_amount = ?, funding_currency = ?, employee_count = ?,
                            last_raise_date = ?, last_raise_stage = ?, fund_tier = ?,
                            focus_areas = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        company_record['name'],
                        company_record['domain'],
                        company_record['yc_batch'],
                        company_record['source'],
                        company_record['messaging_score'],
                        company_record['motion_score'],
                        company_record['market_score'],
                        company_record['stall_probability'],
                        json.dumps(company_record['signals']),
                        company_record['funding_amount'],
                        company_record['funding_currency'],
                        company_record['employee_count'],
                        company_record['last_raise_date'],
                        company_record['last_raise_stage'],
                        company_record['fund_tier'],
                        company_record['focus_areas'],
                        datetime.now(),
                        company_id
                    ))
                # #region agent log
                except Exception as db_err:
                    debug_log("main.py:938", "Portfolio scrape UPDATE error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
                    raise
                # #endregion
            else:
                # #region agent log
                debug_log("main.py:968", "Before portfolio scrape INSERT", {"thread_id": threading.current_thread().ident}, "E")
                # #endregion
                try:
                    conn.execute("""
                        INSERT INTO companies 
                        (id, name, domain, yc_batch, source, messaging_score, motion_score, market_score, 
                         stall_probability, signals, funding_amount, funding_currency, employee_count,
                         last_raise_date, last_raise_stage, fund_tier, focus_areas, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        company_record['id'],
                        company_record['name'],
                        company_record['domain'],
                        company_record['yc_batch'],
                        company_record['source'],
                        company_record['messaging_score'],
                        company_record['motion_score'],
                        company_record['market_score'],
                        company_record['stall_probability'],
                        json.dumps(company_record['signals']),
                        company_record['funding_amount'],
                        company_record['funding_currency'],
                        company_record['employee_count'],
                        company_record['last_raise_date'],
                        company_record['last_raise_stage'],
                        company_record['fund_tier'],
                        company_record['focus_areas'],
                        datetime.now(),
                        datetime.now()
                    ))
                # #region agent log
                except Exception as db_err:
                    debug_log("main.py:968", "Portfolio scrape INSERT error", {"thread_id": threading.current_thread().ident, "error": str(db_err)}, "B")
                    raise
                # #endregion
            
            analyzed_companies.append(CompanyResponse(**company_record))
            analyzed_count += 1
            
            # Rate limiting - small delay between analyses
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"Error analyzing company {company.get('name', 'unknown')}: {e}")
            continue
    
    conn.commit()
    
    print(f"Scraping complete: {len(all_companies)} companies found, {analyzed_count} analyzed, {skipped_count} skipped")
    
    return {
        'scraped_count': len(all_companies),
        'analyzed_count': analyzed_count,
        'skipped_count': skipped_count,
        'portfolios': list(portfolio_results.keys()),
        'companies': [c.dict() for c in analyzed_companies]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

