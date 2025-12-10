"""
Celerio Scout - Backend API
OSINT-powered startup stall detection engine
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import duckdb
import json
import os
from datetime import datetime
from scorer import calculate_scores, scan_company
from seeds import load_mock_data

app = FastAPI(title="Celerio Scout API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DuckDB
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
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
""")

# Load mock data on startup
@app.on_event("startup")
async def startup_event():
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

@app.get("/")
async def root():
    return {"message": "Celerio Scout API", "version": "1.0.0"}

@app.get("/companies", response_model=List[CompanyResponse])
async def get_companies(
    yc_batch: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    vector: Optional[str] = None
):
    """Get all companies with optional filters"""
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    
    if yc_batch:
        query += " AND yc_batch = ?"
        params.append(yc_batch)
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    query += " ORDER BY (messaging_score + motion_score + market_score) / 3 DESC"
    
    results = conn.execute(query, params).fetchall()
    columns = [desc[0] for desc in conn.description]
    
    companies = []
    for row in results:
        company_dict = dict(zip(columns, row))
        # Parse JSON signals
        if isinstance(company_dict.get('signals'), str):
            company_dict['signals'] = json.loads(company_dict['signals'])
        
        # Filter by vector if specified
        if vector:
            if vector == "messaging" and company_dict['messaging_score'] < (min_score or 50):
                continue
            elif vector == "motion" and company_dict['motion_score'] < (min_score or 50):
                continue
            elif vector == "market" and company_dict['market_score'] < (min_score or 50):
                continue
        
        # Format timestamps
        if company_dict.get('created_at'):
            company_dict['created_at'] = str(company_dict['created_at'])
        if company_dict.get('updated_at'):
            company_dict['updated_at'] = str(company_dict['updated_at'])
        
        companies.append(CompanyResponse(**company_dict))
    
    return companies

@app.post("/scan", response_model=CompanyResponse)
async def scan_company_endpoint(request: ScanRequest):
    """Trigger a live scan for a specific URL"""
    try:
        result = await scan_company(request.url)
        
        # Store in database
        existing = conn.execute(
            "SELECT id FROM companies WHERE id = ?",
            (result['id'],)
        ).fetchone()
        
        if existing:
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
                result.get('source', 'scanned'),
                result['messaging_score'],
                result['motion_score'],
                result['market_score'],
                result['stall_probability'],
                json.dumps(result.get('signals', {})),
                datetime.now(),
                result['id']
            ))
        else:
            conn.execute("""
                INSERT INTO companies 
                (id, name, domain, yc_batch, source, messaging_score, motion_score, market_score, stall_probability, signals, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['id'],
                result['name'],
                result['domain'],
                result.get('yc_batch', ''),
                result.get('source', 'scanned'),
                result['messaging_score'],
                result['motion_score'],
                result['market_score'],
                result['stall_probability'],
                json.dumps(result.get('signals', {})),
                datetime.now(),
                datetime.now()
            ))
        conn.commit()
        
        return CompanyResponse(**result)
    except Exception as e:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

