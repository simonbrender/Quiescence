# Investor-Company Relationship Schema Implementation

## Status: ✅ COMPLETE

All components of the investor-company relationship schema have been successfully implemented.

## What Was Implemented

### 1. Database Schema ✅

**New Tables Created:**
- `company_investments` - Junction table linking companies to investors with temporal validity
- `funding_rounds` - Detailed funding round tracking
- `funding_round_investors` - Many-to-many relationship between rounds and investors

**Indexes Created:**
- `idx_company_investments_company` - Fast company lookups
- `idx_company_investments_investor` - Fast investor lookups
- `idx_company_investments_validity` - Temporal queries
- `idx_funding_rounds_company` - Company funding history
- `idx_funding_rounds_date` - Date-based queries

### 2. Migration Script ✅

**File**: `backend/migrate_source_to_relationships.py`

- Converts existing `company.source` field to proper relationships
- Maps YC/Antler sources to VC records
- Creates `company_investments` records for all existing companies
- Preserves `source` field for backward compatibility

**Usage:**
```bash
# Via API (recommended when backend is running)
POST http://localhost:8000/migrate/investor-relationships

# Or directly
python backend/migrate_source_to_relationships.py
```

### 3. Portfolio Scraper Integration ✅

**Updated**: `backend/main.py` (scrape_portfolios function)

- Automatically creates investment relationships when scraping portfolios
- Maps companies to their source VC/investor
- Creates `company_investments` records with proper investment types
- Handles accelerator vs VC distinctions

### 4. API Endpoints ✅

**New Endpoints:**

1. **`GET /companies/{company_id}/investors`**
   - Get all investors for a company
   - Returns investment details, dates, amounts

2. **`GET /investors/{investor_id}/portfolio`**
   - Get all companies in an investor's portfolio
   - Returns company details with investment info

3. **`GET /companies/{company_id}/funding-rounds`**
   - Get complete funding history for a company
   - Includes all rounds with investor details

4. **`POST /companies/{company_id}/investments`**
   - Manually add investment relationship
   - Supports all investment fields

5. **`POST /migrate/investor-relationships`**
   - Run migration to convert source data to relationships

### 5. Graph Database Integration ✅

**File**: `backend/graph_db.py`

- Neo4j support (primary)
- FalkorDB support (alternative)
- Sync function: `sync_duckdb_to_graph()`
- Path finding: `find_investment_path()`
- Co-investor discovery: `find_co_investors()`

**Graph Endpoints:**

1. **`POST /graph/sync`**
   - Sync DuckDB data to graph database
   - Creates/updates nodes and relationships

2. **`GET /investors/{investor_id}/co-investors`**
   - Find VCs that co-invest (uses graph DB if available)
   - Falls back to relational query if graph DB unavailable

3. **`GET /companies/{company_id1}/path-to/{company_id2}`**
   - Find path between companies through shared investors
   - Requires graph database

### 6. Dependencies ✅

**Updated**: `backend/requirements.txt`
- Added `neo4j>=5.0.0` for graph database support

## Database Schema Details

### company_investments Table
```sql
- id: INTEGER PRIMARY KEY
- company_id: INTEGER (FK to companies)
- investor_id: INTEGER (FK to vcs)
- investment_type: TEXT ('direct', 'portfolio', 'accelerator_batch')
- funding_round: TEXT ('Seed', 'Series A', etc.)
- funding_amount: REAL
- funding_currency: TEXT (default 'USD')
- investment_date: DATE
- valid_from: DATE (temporal validity start)
- valid_to: DATE (NULL = active)
- ownership_percentage: REAL
- lead_investor: BOOLEAN
- notes: TEXT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### funding_rounds Table
```sql
- id: INTEGER PRIMARY KEY
- company_id: INTEGER (FK to companies)
- round_name: TEXT
- round_date: DATE
- amount: REAL
- currency: TEXT
- valuation: REAL (post-money)
- lead_investor_id: INTEGER (FK to vcs)
- investor_count: INTEGER
- created_at: TIMESTAMP
```

### funding_round_investors Table
```sql
- id: INTEGER PRIMARY KEY
- funding_round_id: INTEGER (FK to funding_rounds)
- investor_id: INTEGER (FK to vcs)
- amount: REAL (this investor's portion)
- lead_investor: BOOLEAN
- created_at: TIMESTAMP
```

## Graph Database Schema

### Nodes
- **Company**: {id, name, domain, created_at}
- **Investor**: {id, firm_name, type}
- **FundingRound**: {id, round_name, amount, date}

### Relationships
- **(Company)-[:INVESTED_BY]->(Investor)**: {investment_type, funding_round, amount, date, lead_investor, valid_from, valid_to}
- **(Company)-[:HAS_ROUND]->(FundingRound)**
- **(FundingRound)-[:INCLUDES]->(Investor)**: {amount, lead_investor}

## Usage Examples

### Get all investors for a company
```bash
GET http://localhost:8000/companies/5/investors
```

### Get all companies for an investor
```bash
GET http://localhost:8000/investors/1/portfolio
```

### Get funding history
```bash
GET http://localhost:8000/companies/5/funding-rounds
```

### Add investment relationship
```bash
POST http://localhost:8000/companies/5/investments
{
  "investor_id": 1,
  "investment_type": "portfolio",
  "funding_round": "Series A",
  "funding_amount": 5000000,
  "lead_investor": true
}
```

### Sync to graph database
```bash
POST http://localhost:8000/graph/sync
```

### Find co-investors
```bash
GET http://localhost:8000/investors/1/co-investors?limit=10
```

## Environment Variables

For graph database (optional):
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Or FalkorDB (Redis Graph)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
GRAPH_DB_TYPE=neo4j  # or "falkor"
```

## Next Steps

1. **Run Migration**: Execute migration to convert existing data
   ```bash
   POST http://localhost:8000/migrate/investor-relationships
   ```

2. **Set Up Graph DB** (optional):
   - Install Neo4j: https://neo4j.com/download/
   - Or install Redis with FalkorDB module
   - Set environment variables
   - Run sync: `POST /graph/sync`

3. **Frontend Integration** (optional):
   - Display investor relationships in company details
   - Show portfolio view for investors
   - Visualize investment networks

## Files Modified

1. `backend/main.py` - Added tables, endpoints, portfolio scraper integration
2. `backend/migrate_source_to_relationships.py` - Migration script (new)
3. `backend/graph_db.py` - Graph database integration (new)
4. `backend/requirements.txt` - Added neo4j dependency

## Testing

To test the implementation:

1. **Test migration**:
   ```bash
   curl -X POST http://localhost:8000/migrate/investor-relationships
   ```

2. **Test endpoints**:
   ```bash
   # Get investors for a company
   curl http://localhost:8000/companies/5/investors
   
   # Get portfolio for an investor
   curl http://localhost:8000/investors/1/portfolio
   ```

3. **Verify relationships**:
   ```sql
   SELECT COUNT(*) FROM company_investments;
   SELECT * FROM company_investments LIMIT 10;
   ```

---

**Implementation Date**: 2025-12-11  
**Status**: ✅ Complete and Ready for Use

