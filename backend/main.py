"""
Celerio Scout - Backend API
OSINT-powered startup stall detection engine
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json as json_module
from pydantic import BaseModel
from typing import List, Optional, Dict
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
from discovery_sources import DiscoverySourceManager

# Global lock to prevent concurrent portfolio scraping
# Note: asyncio.Lock() must be created in async context, so we use a threading lock for checking
_portfolio_scraping_active = threading.Lock()
_active_scraping_tasks = set()
_scraping_in_progress = False
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

# Initialize Discovery Source Manager
discovery_source_manager = DiscoverySourceManager(conn)

# Investor-Company relationship tables
conn.execute("""
    CREATE TABLE IF NOT EXISTS company_investments (
        id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        investor_id INTEGER NOT NULL,
        investment_type TEXT,
        funding_round TEXT,
        funding_amount REAL,
        funding_currency TEXT DEFAULT 'USD',
        investment_date DATE,
        valid_from DATE DEFAULT CURRENT_DATE,
        valid_to DATE,
        ownership_percentage REAL,
        lead_investor BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS funding_rounds (
        id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        round_name TEXT,
        round_date DATE,
        amount REAL,
        currency TEXT DEFAULT 'USD',
        valuation REAL,
        lead_investor_id INTEGER,
        investor_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS funding_round_investors (
        id INTEGER PRIMARY KEY,
        funding_round_id INTEGER NOT NULL,
        investor_id INTEGER NOT NULL,
        amount REAL,
        lead_investor BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create indexes for performance
try:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_company_investments_company ON company_investments(company_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_company_investments_investor ON company_investments(investor_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_company_investments_validity ON company_investments(valid_from, valid_to)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_funding_rounds_company ON funding_rounds(company_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_funding_rounds_date ON funding_rounds(round_date)")
except Exception as e:
    # Indexes might already exist, continue
    print(f"Note: Some indexes may already exist: {e}")

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
    exclude_mock: Optional[bool] = False,
    limit: Optional[int] = None
):
    """Get all companies with optional filters"""
    try:
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
            # Exclude mock/test data - only exclude companies with source='mock' or test domains
            # Allow real portfolio companies (yc, antler, github, scanned, etc.)
            query += " AND source != 'mock' AND domain NOT LIKE 'test%' AND domain NOT LIKE '%.test'"
        
        # Order by average score, handling NULL scores (treat as 0 for ordering)
        # Use COALESCE to handle NULL values in ORDER BY
        query += " ORDER BY COALESCE((messaging_score + motion_score + market_score) / 3, 0) DESC, id ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        # #region agent log
        debug_log("main.py:305", "Before conn.execute", {"thread_id": threading.current_thread().ident, "query": query[:100]}, "A")
        # #endregion
        try:
            results = conn.execute(query, params).fetchall()
            columns = [desc[0] for desc in conn.description]
        except Exception as db_err:
            debug_log("main.py:305", "conn.execute error", {"thread_id": threading.current_thread().ident, "error": str(db_err), "error_type": type(db_err).__name__}, "A")
            raise HTTPException(status_code=500, detail=f"Database query error: {str(db_err)}")
        
        debug_log("main.py:305", "After conn.execute", {"thread_id": threading.current_thread().ident, "result_count": len(results)}, "A")
        # #endregion
        
        companies = []
        for row in results:
            try:
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
                
                # Ensure scores are not None (default to 0.0 for Pydantic validation)
                if company_dict.get('messaging_score') is None:
                    company_dict['messaging_score'] = 0.0
                if company_dict.get('motion_score') is None:
                    company_dict['motion_score'] = 0.0
                if company_dict.get('market_score') is None:
                    company_dict['market_score'] = 0.0
                
                companies.append(CompanyResponse(**company_dict))
            except Exception as e:
                debug_log("main.py:515", "Error processing company row", {"thread_id": threading.current_thread().ident, "error": str(e), "error_type": type(e).__name__}, "B")
                # Skip this company and continue with the next one
                continue
        
        return companies
    except HTTPException:
        raise
    except Exception as e:
        debug_log("main.py:517", "get_companies exception", {"thread_id": threading.current_thread().ident, "error": str(e), "error_type": type(e).__name__}, "B")
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")

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
    try:
        # #region agent log
        debug_log("main.py:365", "advanced_search entry", {"thread_id": threading.current_thread().ident, "has_free_text": bool(request.free_text_query)}, "A")
        # #endregion
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
        
        # Initialize query - always needed regardless of free_text_query
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
                    # Match exact stage OR companies with yc_batch (portfolio companies are typically Seed)
                    # Allow NULL stages if yc_batch exists (YC companies are typically Seed stage)
                    query += f" AND (last_raise_stage IN ({placeholders}) OR (yc_batch IS NOT NULL AND last_raise_stage IS NULL))"
                    params.extend(request.stages)
                    filters_applied = True
                    print(f"[ADVANCED-SEARCH] Applied stages filter: {request.stages} (including YC companies)")
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
                        # focus_areas is stored as JSON array like ["AI/ML", "B2B SaaS"]
                        # Search for both JSON format and plain text
                        # Also allow NULL/empty focus_areas to match (companies without focus data)
                        focus_conditions.append("(focus_areas LIKE ? OR focus_areas LIKE ? OR focus_areas IS NULL OR focus_areas = '' OR focus_areas = '[]')")
                        params.append(f'%"{focus}"%')  # JSON format: ["AI/ML"]
                        params.append(f'%{focus}%')  # Plain text format
                    if focus_conditions:
                        query += " AND (" + " OR ".join(focus_conditions) + ")"
                        filters_applied = True
                        print(f"[ADVANCED-SEARCH] Applied focus_areas filter: {request.focus_areas} (allowing NULL/empty)")
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
        
        # If no filters were applied, check if we should return companies anyway
        # For portfolio queries or when only rank_by_stall is requested, return companies
        if not filters_applied:
            if request.rank_by_stall and not any([request.stages, request.focus_areas, request.funding_min, 
                                                   request.funding_max, request.employees_min, request.employees_max,
                                                   request.months_post_raise_min, request.months_post_raise_max, request.fund_tiers]):
                # Only rank_by_stall requested - return all companies ranked by stall
                print(f"[ADVANCED-SEARCH] Only rank_by_stall requested, returning all companies")
                query = "SELECT * FROM companies WHERE 1=1"
                params = []
                filters_applied = True  # Allow query to proceed
            else:
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
        # #endregion
        results = None
        columns = None
        try:
            results = conn.execute(query, params).fetchall()
            columns = [desc[0] for desc in conn.description]
            debug_log("main.py:680", "After advanced_search conn.execute", {"thread_id": threading.current_thread().ident, "result_count": len(results)}, "A")
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
                        columns = [desc[0] for desc in conn.description]
                        debug_log("main.py:680", "Query succeeded after adding columns", {"thread_id": threading.current_thread().ident, "result_count": len(results)}, "B")
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
                        columns = [desc[0] for desc in conn.description]
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
                    columns = [desc[0] for desc in conn.description]
                    print(f"[ADVANCED-SEARCH] Using safe query without new columns, found {len(results)} companies")
            else:
                # Re-raise non-column errors as HTTPException
                raise HTTPException(status_code=500, detail=f"Database query error: {error_str}")
    
        # Ensure results and columns are available
        if results is None or columns is None:
            raise HTTPException(status_code=500, detail="Failed to execute database query")
        
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
            
            # Ensure scores are not None (default to 0.0 for Pydantic validation)
            if company_dict.get('messaging_score') is None:
                company_dict['messaging_score'] = 0.0
            if company_dict.get('motion_score') is None:
                company_dict['motion_score'] = 0.0
            if company_dict.get('market_score') is None:
                company_dict['market_score'] = 0.0
            
            try:
                companies.append(CompanyResponse(**company_dict))
            except Exception as e:
                debug_log("main.py:925", "Error creating CompanyResponse", {"thread_id": threading.current_thread().ident, "error": str(e), "error_type": type(e).__name__}, "B")
                # Skip this company and continue with the next one
                continue
        
        return companies
    except HTTPException:
        raise
    except Exception as e:
        debug_log("main.py:930", "advanced_search exception", {"thread_id": threading.current_thread().ident, "error": str(e), "error_type": type(e).__name__}, "B")
        raise HTTPException(status_code=500, detail=f"Error performing advanced search: {str(e)}")

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
        
        # First, try searching the database with parsed parameters (fast path)
        print(f"[FREE-TEXT] First searching database with parsed criteria: {json.dumps(parsed_params, indent=2)}")
        if progress_callback:
            progress_callback({
                'type': 'database_search_started',
                'message': 'Searching database...',
                'criteria': parsed_params,
                'timestamp': datetime.now().isoformat()
            })
        
        # Build and execute database query directly (avoid web discovery timeout)
        try:
            db_query = "SELECT * FROM companies WHERE 1=1"
            db_params = []
            has_filters = False
            
            # Filter by stage
            if parsed_params.get('stages') and column_exists('companies', 'last_raise_stage'):
                placeholders = ','.join(['?' for _ in parsed_params['stages']])
                db_query += f" AND (last_raise_stage IN ({placeholders}) OR (yc_batch IS NOT NULL AND last_raise_stage IS NULL))"
                db_params.extend(parsed_params['stages'])
                has_filters = True
            
            # Filter by focus areas
            if parsed_params.get('focus_areas') and column_exists('companies', 'focus_areas'):
                focus_conditions = []
                for focus in parsed_params['focus_areas']:
                    focus_conditions.append("(focus_areas LIKE ? OR focus_areas LIKE ? OR focus_areas IS NULL OR focus_areas = '' OR focus_areas = '[]')")
                    db_params.append(f'%"{focus}"%')
                    db_params.append(f'%{focus}%')
                if focus_conditions:
                    db_query += " AND (" + " OR ".join(focus_conditions) + ")"
                    has_filters = True
            
            # Add ranking
            if parsed_params.get('rank_by_stall', True):
                db_query += """ ORDER BY 
                (messaging_score + motion_score + market_score) / 3 ASC,
                CASE stall_probability 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                    ELSE 4 
                END ASC"""
            else:
                db_query += " ORDER BY (messaging_score + motion_score + market_score) / 3 DESC"
            
            db_query += " LIMIT 1000"  # Limit results
            
            # Execute query
            if has_filters or not parsed_params.get('is_portfolio_query'):
                db_results_raw = conn.execute(db_query, db_params).fetchall()
                db_columns = [desc[0] for desc in conn.description]
                db_results = []
                for row in db_results_raw:
                    company_dict = dict(zip(db_columns, row))
                    # Convert focus_areas from JSON string to list if needed
                    if company_dict.get('focus_areas') and isinstance(company_dict['focus_areas'], str):
                        try:
                            company_dict['focus_areas'] = json.loads(company_dict['focus_areas'])
                        except:
                            pass
                    db_results.append(company_dict)
                
                print(f"[FREE-TEXT] Database search found {len(db_results)} companies")
                if db_results and len(db_results) > 0:
                    # Return database results immediately - no need for web discovery
                    if progress_callback:
                        progress_callback({
                            'type': 'search_complete',
                            'companies_found': len(db_results),
                            'message': f'Found {len(db_results)} companies in database',
                            'timestamp': datetime.now().isoformat()
                        })
                    print(f"[FREE-TEXT] Returning {len(db_results)} companies from database")
                    return db_results
        except Exception as e:
            print(f"[FREE-TEXT] Error searching database: {e}")
            import traceback
            traceback.print_exc()
        
        # Only do web discovery if database search returned no results AND it's not a portfolio query
        if parsed_params.get('is_portfolio_query'):
            print(f"[FREE-TEXT] Portfolio query detected - will scrape portfolios")
        else:
            print(f"[FREE-TEXT] No database results found - skipping web discovery for now (to avoid timeout)")
            # Return empty results rather than timing out on web discovery
            if progress_callback:
                progress_callback({
                    'type': 'search_complete',
                    'companies_found': 0,
                    'message': 'No companies found in database. Web discovery disabled to prevent timeouts.',
                    'timestamp': datetime.now().isoformat()
                })
            return []
        
        # Discover companies from web sources based on parsed criteria (only for portfolio queries)
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
                # Check if scraping is already in progress BEFORE starting new task
                with _portfolio_scraping_active:
                    if _scraping_in_progress:
                        print(f"[FREE-TEXT] Portfolio scraping already in progress, skipping duplicate request")
                        from fastapi.responses import JSONResponse
                        return JSONResponse(
                            content=[],
                            headers={"X-Session-ID": session_id, "X-Status": "already-scraping"}
                        )
                    _scraping_in_progress = True
                    print(f"[FREE-TEXT] Portfolio query - starting background scraping task (lock acquired)")
                
                # Start scraping in background task
                import asyncio
                async def background_scrape():
                    saved_count = 0
                    batch_size = 10  # Save companies in batches of 10
                    companies_batch = []
                    
                    def batch_progress_callback(event):
                        """Wrapper that intercepts progress events and saves companies in batches"""
                        nonlocal saved_count, companies_batch
                        
                        # Check if this event contains companies to save
                        if event.get('type') == 'progress' and 'companies_batch' in event:
                            batch = event.get('companies_batch', [])
                            if batch:
                                companies_batch.extend(batch)
                                
                                # Save batch when it reaches batch_size
                                if len(companies_batch) >= batch_size:
                                    saved = _save_companies_batch(companies_batch[:batch_size])
                                    saved_count += saved
                                    companies_batch = companies_batch[batch_size:]
                                    
                                    # Emit companies_added event
                                    if progress_callback:
                                        progress_callback({
                                            'type': 'companies_added',
                                            'companies': companies_batch[:batch_size],
                                            'total_saved': saved_count,
                                            'message': f'Saved {saved} companies to database (total: {saved_count})',
                                            'timestamp': datetime.now().isoformat()
                                        })
                        
                        # Forward all events to original callback
                        if progress_callback:
                            progress_callback(event)
                    
                    def _save_companies_batch(batch):
                        """Save a batch of companies to database"""
                        saved = 0
                        for company in batch:
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
                                    # Ensure columns exist
                                    for col_name, col_type in required_columns:
                                        if not column_exists('companies', col_name):
                                            try:
                                                conn.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
                                                conn.commit()
                                            except:
                                                pass
                                    
                                    # Insert company
                                    company_id = abs(hash(domain)) % 1000000
                                    conn.execute("""
                                        INSERT INTO companies 
                                        (id, name, domain, source, last_raise_stage, focus_areas, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        company_id,
                                        company.get('name', ''),
                                        domain,
                                        company.get('source', 'portfolio_scraping'),
                                        company.get('last_raise_stage'),
                                        json.dumps(company.get('focus_areas', [])),
                                        datetime.now(),
                                        datetime.now()
                                    ))
                                    conn.commit()
                                    saved += 1
                            except Exception as e:
                                print(f"[FREE-TEXT] Error saving company batch: {e}")
                                conn.rollback()
                        return saved
                    
                    try:
                        if progress_callback:
                            progress_callback({
                                'type': 'scraping_initiated',
                                'message': 'Background scraping task started',
                                'sources': parsed_params.get('portfolio_sources', []),
                                'timestamp': datetime.now().isoformat()
                            })
                        companies = await discovery.discover_companies(parsed_params, progress_callback=batch_progress_callback)
                        
                        # Save any remaining companies in batch
                        if companies_batch:
                            saved = _save_companies_batch(companies_batch)
                            saved_count += saved
                            if progress_callback:
                                progress_callback({
                                    'type': 'companies_added',
                                    'companies': companies_batch,
                                    'total_saved': saved_count,
                                    'message': f'Saved final batch of {saved} companies',
                                    'timestamp': datetime.now().isoformat()
                                })
                        
                        print(f"[FREE-TEXT] Background scraping completed: {len(companies)} companies found, {saved_count} saved")
                        if progress_callback:
                            progress_callback({
                                'type': 'scraping_complete',
                                'companies_found': len(companies),
                                'companies_saved': saved_count,
                                'message': f'Scraping completed: {len(companies)} companies found, {saved_count} saved to database',
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
                        finally:
                            if task_id:
                                _active_scraping_tasks.discard(task_id)
                            with _portfolio_scraping_active:
                                _scraping_in_progress = False
                            print(f"[FREE-TEXT] Background scraping task {task_id} completed, lock released")
                
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

@app.post("/companies/enrich")
async def enrich_companies_endpoint(batch_size: int = 100, use_firecrawl: bool = True):
    """
    Enrich companies in the database with stage, focus areas, employees, and funding data.
    Runs enrichment in background and returns immediately.
    """
    try:
        import asyncio
        from enrich_existing_companies import enrich_company_batch
        
        print("[ENRICH-API] Starting batch enrichment in background...")
        
        # Get companies that need enrichment
        companies = conn.execute("""
            SELECT id, name, domain, source, yc_batch, last_raise_stage, 
                   focus_areas, employee_count, funding_amount
            FROM companies
            WHERE last_raise_stage IS NULL OR focus_areas IS NULL OR focus_areas = '' OR focus_areas = '[]'
            ORDER BY created_at DESC
            LIMIT ?
        """, (batch_size,)).fetchall()
        
        columns = ['id', 'name', 'domain', 'source', 'yc_batch', 'last_raise_stage',
                  'focus_areas', 'employee_count', 'funding_amount']
        company_dicts = [dict(zip(columns, row)) for row in companies]
        
        total = len(company_dicts)
        print(f"[ENRICH-API] Found {total} companies to enrich (batch size: {batch_size})")
        
        if total == 0:
            return {
                "status": "success",
                "message": "No companies need enrichment",
                "total_companies": 0,
                "enriched": 0,
                "updated": 0
            }
        
        # Run enrichment in background task
        async def enrich_background():
            try:
                enriched, updated = await enrich_company_batch(conn, company_dicts)
                print(f"[ENRICH-API] Background enrichment completed: {enriched} processed, {updated} updated")
            except Exception as e:
                print(f"[ENRICH-API] Background enrichment error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start background task
        asyncio.create_task(enrich_background())
        
        # Return immediately
        return {
            "status": "started",
            "message": f"Enrichment started in background for {total} companies",
            "total_companies": total,
            "batch_size": batch_size
        }
    except Exception as e:
        print(f"[ENRICH-API] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enrichment error: {str(e)}")


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

@app.post("/migrate/investor-relationships")
async def migrate_investor_relationships():
    """
    Run migration to convert company.source to investor-company relationships.
    This is a one-time migration that can be run via API.
    """
    try:
        from migrate_source_to_relationships import migrate_companies
        migrate_companies(conn)
        return {"status": "success", "message": "Migration completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")

@app.get("/companies/{company_id}/investors")
async def get_company_investors(company_id: int):
    """Get all investors for a specific company"""
    try:
        results = conn.execute("""
            SELECT 
                ci.id,
                ci.investment_type,
                ci.funding_round,
                ci.funding_amount,
                ci.funding_currency,
                ci.investment_date,
                ci.lead_investor,
                ci.valid_from,
                ci.valid_to,
                v.id as investor_id,
                v.firm_name,
                v.type as investor_type,
                v.stage as investor_stage
            FROM company_investments ci
            JOIN vcs v ON ci.investor_id = v.id
            WHERE ci.company_id = ? AND (ci.valid_to IS NULL OR ci.valid_to >= CURRENT_DATE)
            ORDER BY ci.investment_date DESC NULLS LAST, ci.created_at DESC
        """, (company_id,)).fetchall()
        
        investors = []
        for row in results:
            investors.append({
                "investment_id": row[0],
                "investment_type": row[1],
                "funding_round": row[2],
                "funding_amount": row[3],
                "funding_currency": row[4],
                "investment_date": str(row[5]) if row[5] else None,
                "lead_investor": bool(row[6]),
                "valid_from": str(row[7]) if row[7] else None,
                "valid_to": str(row[8]) if row[8] else None,
                "investor": {
                    "id": row[9],
                    "firm_name": row[10],
                    "type": row[11],
                    "stage": row[12]
                }
            })
        
        return investors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching investors: {str(e)}")

@app.get("/investors")
async def get_investors():
    """Get all investors"""
    try:
        results = conn.execute("""
            SELECT id, firm_name, type, stage, domain, url, focus_areas, created_at
            FROM vcs
            ORDER BY firm_name
        """).fetchall()
        
        investors = []
        for row in results:
            investors.append({
                "id": row[0],
                "firm_name": row[1],
                "type": row[2],
                "stage": row[3],
                "domain": row[4],
                "url": row[5],
                "focus_areas": json.loads(row[6]) if row[6] and isinstance(row[6], str) else (row[6] if row[6] else []),
                "created_at": str(row[7]) if row[7] else None,
            })
        
        return investors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching investors: {str(e)}")

@app.get("/investors/relationships")
async def get_investor_relationships():
    """Get all investment relationships"""
    try:
        results = conn.execute("""
            SELECT 
                ci.id,
                ci.company_id,
                ci.investor_id,
                ci.investment_type,
                ci.funding_round,
                ci.funding_amount,
                ci.investment_date,
                ci.lead_investor,
                v.firm_name,
                c.name as company_name
            FROM company_investments ci
            JOIN vcs v ON ci.investor_id = v.id
            JOIN companies c ON ci.company_id = c.id
            WHERE ci.valid_to IS NULL OR ci.valid_to >= CURRENT_DATE
            ORDER BY ci.investment_date DESC NULLS LAST
        """).fetchall()
        
        relationships = []
        for row in results:
            relationships.append({
                "id": row[0],
                "company_id": row[1],
                "investor_id": row[2],
                "investment_type": row[3],
                "funding_round": row[4],
                "funding_amount": row[5],
                "investment_date": str(row[6]) if row[6] else None,
                "lead_investor": bool(row[7]),
                "investor_name": row[8],
                "company_name": row[9],
            })
        
        return relationships
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching relationships: {str(e)}")

@app.get("/investors/{investor_id}/portfolio")
async def get_investor_portfolio(investor_id: int):
    """Get all companies for a specific investor"""
    try:
        results = conn.execute("""
            SELECT 
                c.id,
                c.name,
                c.domain,
                c.source,
                c.yc_batch,
                c.messaging_score,
                c.motion_score,
                c.market_score,
                c.stall_probability,
                ci.investment_type,
                ci.funding_round,
                ci.funding_amount,
                ci.investment_date,
                ci.lead_investor
            FROM company_investments ci
            JOIN companies c ON ci.company_id = c.id
            WHERE ci.investor_id = ? AND (ci.valid_to IS NULL OR ci.valid_to >= CURRENT_DATE)
            ORDER BY ci.investment_date DESC NULLS LAST, c.created_at DESC
        """, (investor_id,)).fetchall()
        
        companies = []
        for row in results:
            companies.append({
                "id": row[0],
                "name": row[1],
                "domain": row[2],
                "source": row[3],
                "yc_batch": row[4],
                "messaging_score": row[5],
                "motion_score": row[6],
                "market_score": row[7],
                "stall_probability": row[8],
                "investment_type": row[9],
                "funding_round": row[10],
                "funding_amount": row[11],
                "investment_date": str(row[12]) if row[12] else None,
                "lead_investor": bool(row[13])
            })
        
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")

@app.get("/companies/{company_id}/funding-rounds")
async def get_company_funding_rounds(company_id: int):
    """Get funding history for a specific company"""
    try:
        # Get funding rounds
        rounds = conn.execute("""
            SELECT 
                fr.id,
                fr.round_name,
                fr.round_date,
                fr.amount,
                fr.currency,
                fr.valuation,
                fr.lead_investor_id,
                fr.investor_count,
                v.firm_name as lead_investor_name
            FROM funding_rounds fr
            LEFT JOIN vcs v ON fr.lead_investor_id = v.id
            WHERE fr.company_id = ?
            ORDER BY fr.round_date DESC NULLS LAST
        """, (company_id,)).fetchall()
        
        funding_rounds = []
        for round_row in rounds:
            round_id = round_row[0]
            
            # Get investors for this round
            investors = conn.execute("""
                SELECT 
                    v.id,
                    v.firm_name,
                    v.type,
                    fri.amount,
                    fri.lead_investor
                FROM funding_round_investors fri
                JOIN vcs v ON fri.investor_id = v.id
                WHERE fri.funding_round_id = ?
            """, (round_id,)).fetchall()
            
            round_investors = []
            for inv_row in investors:
                round_investors.append({
                    "id": inv_row[0],
                    "firm_name": inv_row[1],
                    "type": inv_row[2],
                    "amount": inv_row[3],
                    "lead_investor": bool(inv_row[4])
                })
            
            funding_rounds.append({
                "id": round_id,
                "round_name": round_row[1],
                "round_date": str(round_row[2]) if round_row[2] else None,
                "amount": round_row[3],
                "currency": round_row[4],
                "valuation": round_row[5],
                "lead_investor_id": round_row[6],
                "lead_investor_name": round_row[8],
                "investor_count": round_row[7],
                "investors": round_investors
            })
        
        return funding_rounds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching funding rounds: {str(e)}")

@app.post("/companies/{company_id}/investments")
async def add_company_investment(
    company_id: int,
    investor_id: int,
    investment_type: str,
    funding_round: Optional[str] = None,
    funding_amount: Optional[float] = None,
    funding_currency: str = "USD",
    investment_date: Optional[date] = None,
    lead_investor: bool = False,
    notes: Optional[str] = None
):
    """Add an investment relationship between a company and investor"""
    try:
        # Verify company exists
        company = conn.execute("SELECT id FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Verify investor exists
        investor = conn.execute("SELECT id FROM vcs WHERE id = ?", (investor_id,)).fetchone()
        if not investor:
            raise HTTPException(status_code=404, detail="Investor not found")
        
        # Create investment relationship
        conn.execute("""
            INSERT INTO company_investments 
            (company_id, investor_id, investment_type, funding_round, funding_amount, 
             funding_currency, investment_date, valid_from, lead_investor, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            investor_id,
            investment_type,
            funding_round,
            funding_amount,
            funding_currency,
            investment_date,
            datetime.now().date(),
            None,  # valid_to (NULL = active)
            lead_investor,
            notes,
            datetime.now(),
            datetime.now()
        ))
        conn.commit()
        
        return {"status": "success", "message": "Investment relationship created"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating investment: {str(e)}")

@app.post("/graph/sync")
async def sync_graph_database():
    """
    Sync DuckDB data to graph database (Neo4j/FalkorDB).
    This creates/updates graph nodes and relationships.
    """
    try:
        from graph_db import GraphDB, sync_duckdb_to_graph
        
        db_type = os.getenv("GRAPH_DB_TYPE", "neo4j")  # "neo4j" or "falkor"
        graph_db = GraphDB(db_type=db_type)
        
        if not graph_db.driver and not graph_db.graph:
            raise HTTPException(
                status_code=503,
                detail="Graph database not configured. Set NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD or REDIS_HOST/REDIS_PORT environment variables."
            )
        
        sync_duckdb_to_graph(conn, graph_db)
        graph_db.close()
        
        return {"status": "success", "message": "Graph database synced successfully"}
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Graph database drivers not installed. Install neo4j package: pip install neo4j"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.get("/investors/{investor_id}/co-investors")
async def get_co_investors(investor_id: int, limit: int = 10):
    """Get VCs that co-invest with a given investor (using graph database)"""
    try:
        from graph_db import GraphDB
        
        db_type = os.getenv("GRAPH_DB_TYPE", "neo4j")
        graph_db = GraphDB(db_type=db_type)
        
        if not graph_db.driver and not graph_db.graph:
            # Fallback to relational query
            results = conn.execute("""
                SELECT 
                    i2.id,
                    i2.firm_name,
                    COUNT(DISTINCT c.id) as co_investment_count
                FROM company_investments ci1
                JOIN companies c ON ci1.company_id = c.id
                JOIN company_investments ci2 ON c.id = ci2.company_id
                JOIN vcs i1 ON ci1.investor_id = i1.id
                JOIN vcs i2 ON ci2.investor_id = i2.id
                WHERE i1.id = ? AND i2.id <> i1.id
                GROUP BY i2.id, i2.firm_name
                ORDER BY co_investment_count DESC
                LIMIT ?
            """, (investor_id, limit)).fetchall()
            
            return [{
                "investor_id": row[0],
                "firm_name": row[1],
                "co_investment_count": row[2]
            } for row in results]
        
        co_investors = graph_db.find_co_investors(investor_id, limit)
        graph_db.close()
        
        return co_investors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding co-investors: {str(e)}")

@app.get("/companies/{company_id1}/path-to/{company_id2}")
async def get_company_path(company_id1: int, company_id2: int, max_depth: int = 3):
    """Find path between two companies through shared investors (using graph database)"""
    try:
        from graph_db import GraphDB
        
        db_type = os.getenv("GRAPH_DB_TYPE", "neo4j")
        graph_db = GraphDB(db_type=db_type)
        
        if not graph_db.driver and not graph_db.graph:
            raise HTTPException(
                status_code=503,
                detail="Graph database not available for path finding"
            )
        
        path = graph_db.find_investment_path(company_id1, company_id2, max_depth)
        graph_db.close()
        
        if path:
            return path
        else:
            return {"message": "No path found", "path": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding path: {str(e)}")

@app.get("/companies/export")
async def export_all_companies():
    """
    Export all companies without any filtering or transformation.
    Returns raw company data for CSV export.
    """
    try:
        # Get all companies without any filters or transformations
        query = "SELECT * FROM companies ORDER BY id"
        results = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        companies = []
        for row in results:
            company_dict = dict(zip(columns, row))
            # Keep raw values - don't transform funding_amount or scores
            # Only parse JSON fields that need parsing
            if isinstance(company_dict.get('signals'), str) and company_dict.get('signals'):
                try:
                    company_dict['signals'] = json.loads(company_dict['signals'])
                except:
                    company_dict['signals'] = {}
            
            if isinstance(company_dict.get('focus_areas'), str) and company_dict.get('focus_areas'):
                try:
                    company_dict['focus_areas'] = json.loads(company_dict['focus_areas'])
                except:
                    company_dict['focus_areas'] = []
            
            # Convert dates to strings for JSON serialization
            if company_dict.get('created_at'):
                company_dict['created_at'] = str(company_dict['created_at'])
            if company_dict.get('updated_at'):
                company_dict['updated_at'] = str(company_dict['updated_at'])
            if company_dict.get('last_raise_date'):
                company_dict['last_raise_date'] = str(company_dict['last_raise_date'])
            
            companies.append(company_dict)
        
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

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

class DiscoverySourceRequest(BaseModel):
    name: str
    url: str
    source_type: str = "VC"
    discovery_method: str = "scrape"
    priority: int = 100
    enabled: bool = True
    config: Optional[Dict] = {}

class DiscoverySourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    discovery_method: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    config: Optional[Dict] = None

@app.get("/discovery/sources")
async def get_discovery_sources(enabled_only: bool = False):
    """Get all discovery sources"""
    sources = discovery_source_manager.get_all_sources(enabled_only=enabled_only)
    return {"sources": sources}

@app.post("/discovery/sources")
async def add_discovery_source(source: DiscoverySourceRequest):
    """Add a new discovery source"""
    try:
        source_dict = source.dict()
        source_id = discovery_source_manager.add_source(source_dict)
        return {"id": source_id, "message": "Source added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/discovery/sources/{source_id}")
async def update_discovery_source(source_id: int, updates: DiscoverySourceUpdate):
    """Update a discovery source"""
    try:
        updates_dict = {k: v for k, v in updates.dict().items() if v is not None}
        discovery_source_manager.update_source(source_id, updates_dict)
        return {"message": "Source updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/discovery/sources/{source_id}")
async def delete_discovery_source(source_id: int):
    """Delete a discovery source (user-added only)"""
    try:
        discovery_source_manager.delete_source(source_id)
        return {"message": "Source deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _discover_vcs_with_progress():
    """Internal discovery function that yields progress updates"""
    discovery = VCDiscovery()
    total_layers = 7
    current_layer = 0
    
    # Track stats
    stats = {
        'discovered': 0,
        'added': 0,
        'skipped': 0,
        'errors': 0,
        'vcs': 0,
        'accelerators': 0,
        'studios': 0
    }
    
    discovered_vcs = []
    
    try:
        # Layer 1: Crunchbase
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Discovering from Crunchbase...',
            'layer': f'Layer {current_layer}/7: Crunchbase VC Discovery',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            crunchbase_vcs = await discovery.discover_from_crunchbase_comprehensive()
            discovered_vcs.extend(crunchbase_vcs)
            stats['discovered'] += len(crunchbase_vcs)
            stats['vcs'] += len(crunchbase_vcs)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'Crunchbase: Found {len(crunchbase_vcs)} VCs'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'error',
                'message': f'Crunchbase discovery failed: {str(e)[:100]}'
            }
        
        # Layer 2: F6S
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Discovering accelerators from F6S...',
            'layer': f'Layer {current_layer}/7: F6S Accelerator Discovery',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            f6s_accelerators = await discovery.discover_from_f6s_accelerators()
            discovered_vcs.extend(f6s_accelerators)
            stats['discovered'] += len(f6s_accelerators)
            stats['accelerators'] += len(f6s_accelerators)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'F6S: Found {len(f6s_accelerators)} accelerators'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'error',
                'message': f'F6S discovery failed: {str(e)[:100]}'
            }
        
        # Layer 2.5: StudioHub
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Discovering studios from StudioHub...',
            'layer': f'Layer {current_layer}/7: StudioHub Studio Discovery',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            studiohub_studios = await discovery.discover_from_studiohub()
            discovered_vcs.extend(studiohub_studios)
            stats['discovered'] += len(studiohub_studios)
            stats['studios'] += len(studiohub_studios)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'StudioHub: Found {len(studiohub_studios)} studios'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'error',
                'message': f'StudioHub discovery failed: {str(e)[:100]}'
            }
        
        # Layer 3: VC Lists
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Discovering from VC directories...',
            'layer': f'Layer {current_layer}/7: VC Directory Lists',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            vc_lists = await discovery.discover_from_vc_lists()
            discovered_vcs.extend(vc_lists)
            stats['discovered'] += len(vc_lists)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'Directories: Found {len(vc_lists)} investment vehicles'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'error',
                'message': f'Directory discovery failed: {str(e)[:100]}'
            }
        
        # Layer 4: Google Search
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Searching Google for investment vehicles...',
            'layer': f'Layer {current_layer}/7: Google Search',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            search_queries = [
                "venture capital firms directory",
                "top VC firms",
                "venture studios list",
                "startup accelerators directory",
            ]
            google_results = await discovery.discover_from_google_search(search_queries, max_results_per_query=30)
            discovered_vcs.extend(google_results)
            stats['discovered'] += len(google_results)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'Google Search: Found {len(google_results)} investment vehicles'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'warn',
                'message': f'Google Search discovery failed: {str(e)[:100]}'
            }
        
        # Layer 5: Vertical-Specific
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Discovering vertical-specific investors...',
            'layer': f'Layer {current_layer}/7: Vertical-Specific Discovery',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            verticals = ['FinTech', 'BioTech', 'AI', 'ClimateTech', 'Enterprise SaaS']
            vertical_results = await discovery.discover_from_vertical_specific(verticals)
            discovered_vcs.extend(vertical_results)
            stats['discovered'] += len(vertical_results)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'Vertical-Specific: Found {len(vertical_results)} investment vehicles'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'warn',
                'message': f'Vertical-specific discovery failed: {str(e)[:100]}'
            }
        
        # Layer 6: Regional
        current_layer += 1
        yield {
            'type': 'status',
            'message': f'Discovering from regional directories...',
            'layer': f'Layer {current_layer}/7: Regional Discovery',
            'progress': int((current_layer / total_layers) * 50)
        }
        
        try:
            regional_results = await discovery.discover_from_regional_directories()
            discovered_vcs.extend(regional_results)
            stats['discovered'] += len(regional_results)
            yield {
                'type': 'log',
                'level': 'success',
                'message': f'Regional: Found {len(regional_results)} investment vehicles'
            }
        except Exception as e:
            yield {
                'type': 'log',
                'level': 'warn',
                'message': f'Regional discovery failed: {str(e)[:100]}'
            }
        
        # Processing: Adding to database
        yield {
            'type': 'status',
            'message': f'Processing {len(discovered_vcs)} discovered investment vehicles...',
            'layer': 'Processing: Adding to database',
            'progress': 60
        }
        
        added_count = 0
        skipped_duplicates = 0
        errors = 0
        
        for idx, vc in enumerate(discovered_vcs):
            try:
                firm_name = vc.get('firm_name', '').strip()
                if not firm_name:
                    continue
                
                # Check if VC already exists
                existing = conn.execute(
                    "SELECT id, firm_name FROM vcs WHERE firm_name = ?",
                    (firm_name,)
                ).fetchone()
                
                domain = vc.get('domain', '').strip()
                if not existing and domain:
                    existing = conn.execute(
                        "SELECT id, firm_name FROM vcs WHERE domain = ?",
                        (domain,)
                    ).fetchone()
                
                if existing:
                    skipped_duplicates += 1
                    continue
                
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
                
                # Update progress every 10 items
                if (idx + 1) % 10 == 0:
                    progress = 60 + int((idx + 1) / len(discovered_vcs) * 30)
                    yield {
                        'type': 'progress',
                        'progress': progress
                    }
                    yield {
                        'type': 'stats',
                        'stats': {
                            'discovered': len(discovered_vcs),
                            'added': added_count,
                            'skipped': skipped_duplicates,
                            'errors': errors
                        }
                    }
                    
            except Exception as e:
                errors += 1
                yield {
                    'type': 'log',
                    'level': 'error',
                    'message': f'Error adding VC {vc.get("firm_name", "Unknown")}: {str(e)[:100]}'
                }
        
        conn.commit()
        
        stats['added'] = added_count
        stats['skipped'] = skipped_duplicates
        stats['errors'] = errors
        
        yield {
            'type': 'complete',
            'progress': 100,
            'result': {
                'discovered': len(discovered_vcs),
                'added': added_count,
                'skipped_duplicates': skipped_duplicates,
                'errors': errors,
                'stats': stats
            }
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        yield {
            'type': 'error',
            'message': f'Discovery failed: {str(e)}'
        }

@app.post("/portfolios/discover")
async def discover_vcs():
    """Discover new VCs from web sources (non-streaming, for backward compatibility)"""
    try:
        discovery = VCDiscovery()
        discovered_vcs = await discovery.discover_all()
        
        added_count = 0
        skipped_duplicates = 0
        errors = 0
        
        for vc in discovered_vcs:
            try:
                firm_name = vc.get('firm_name', '').strip()
                if not firm_name:
                    continue
                
                existing = conn.execute(
                    "SELECT id, firm_name FROM vcs WHERE firm_name = ?",
                    (firm_name,)
                ).fetchone()
                
                domain = vc.get('domain', '').strip()
                if not existing and domain:
                    existing = conn.execute(
                        "SELECT id, firm_name FROM vcs WHERE domain = ?",
                        (domain,)
                    ).fetchone()
                
                if existing:
                    skipped_duplicates += 1
                    continue
                
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
                errors += 1
                continue
        
        conn.commit()
        
        return {
            "discovered": len(discovered_vcs),
            "added": added_count,
            "skipped_duplicates": skipped_duplicates,
            "errors": errors,
            "message": f"Discovered {len(discovered_vcs)} VCs, added {added_count} new ones, skipped {skipped_duplicates} duplicates"
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"VC discovery error: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"VC discovery failed: {str(e)}. This operation can take several minutes and may timeout. Please try again or check backend logs."
        )

@app.get("/portfolios/discover/stream")
async def discover_vcs_stream():
    """Discover new VCs with real-time progress updates via Server-Sent Events"""
    async def event_generator():
        try:
            # Send initial connection message
            yield {
                "event": "message",
                "data": json_module.dumps({
                    "type": "status",
                    "message": "Starting discovery process...",
                    "progress": 0
                })
            }
            
            # Start discovery and stream updates
            # Note: _discover_vcs_with_progress() is an async generator
            # We need to properly iterate over it
            discovery_gen = _discover_vcs_with_progress()
            try:
                async for update in discovery_gen:
                    yield {
                        "event": "message",
                        "data": json_module.dumps(update)
                    }
            except StopAsyncIteration:
                # Generator completed normally
                yield {
                    "event": "message",
                    "data": json_module.dumps({
                        "type": "status",
                        "message": "Discovery completed",
                        "progress": 100
                    })
                }
        except GeneratorExit:
            # Client disconnected, cleanup
            print("Client disconnected from discovery stream")
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Discovery stream error: {error_details}")
            try:
                yield {
                    "event": "message",
                    "data": json_module.dumps({
                        "type": "error",
                        "message": f"Discovery failed: {str(e)}"
                    })
                }
            except:
                # If we can't send error, just log it
                pass
    
    return EventSourceResponse(event_generator())

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
    # Build VC name to ID mapping for investment relationships
    vc_name_to_id = {}
    company_to_vc = {}  # Map company to VC firm name
    for firm_name, companies in portfolio_results.items():
        # Get VC ID for this portfolio
        vc_result = conn.execute(
            "SELECT id FROM vcs WHERE firm_name = ?",
            (firm_name,)
        ).fetchone()
        if vc_result:
            vc_name_to_id[firm_name] = vc_result[0]
            # Map each company to this VC
            for company in companies:
                company_key = company.get('domain', '').strip() or company.get('name', '').strip()
                if company_key:
                    company_to_vc[company_key] = firm_name
        
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
            
            # Create investment relationship if this company came from a portfolio
            company_key = domain or company.get('name', '').strip()
            if company_key in company_to_vc:
                vc_firm_name = company_to_vc[company_key]
                investor_id = vc_name_to_id.get(vc_firm_name)
                
                if investor_id:
                    try:
                        # Check if investment relationship already exists
                        existing_inv = conn.execute("""
                            SELECT id FROM company_investments 
                            WHERE company_id = ? AND investor_id = ?
                        """, (company_id, investor_id)).fetchone()
                        
                        if not existing_inv:
                            # Determine investment type based on VC type
                            vc_type_result = conn.execute(
                                "SELECT type FROM vcs WHERE id = ?",
                                (investor_id,)
                            ).fetchone()
                            vc_type = vc_type_result[0] if vc_type_result else 'VC'
                            investment_type = 'accelerator_batch' if vc_type.lower() in ['accelerator', 'studio'] else 'portfolio'
                            
                            # Infer funding round
                            funding_round = company_record.get('last_raise_stage') or 'Seed'
                            
                            # Create investment relationship
                            conn.execute("""
                                INSERT INTO company_investments 
                                (company_id, investor_id, investment_type, funding_round, funding_amount, 
                                 funding_currency, investment_date, valid_from, valid_to, lead_investor, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                company_id,
                                investor_id,
                                investment_type,
                                funding_round,
                                company_record.get('funding_amount'),
                                company_record.get('funding_currency', 'USD'),
                                company_record.get('last_raise_date'),
                                datetime.now().date(),
                                None,  # valid_to (NULL = active)
                                True if investment_type == 'accelerator_batch' else False,  # Lead for accelerators
                                datetime.now(),
                                datetime.now()
                            ))
                    except Exception as inv_err:
                        # Don't fail the whole process if investment creation fails
                        print(f"Warning: Could not create investment relationship for {company_record['name']}: {inv_err}")
            
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

