"""
Migration script to convert existing company.source field to proper investor-company relationships.

This script:
1. Maps existing source values to VC records
2. Creates company_investments records for existing companies
3. Preserves source field for backward compatibility
"""
import duckdb
import json
from pathlib import Path
from datetime import datetime

def get_db_connection():
    """Get DuckDB connection"""
    db_path = Path(__file__).parent / "celerio_scout.db"
    return duckdb.connect(str(db_path))

def ensure_vc_exists(conn, firm_name, vc_data=None):
    """Ensure a VC record exists, create if missing"""
    existing = conn.execute(
        "SELECT id FROM vcs WHERE firm_name = ?",
        (firm_name,)
    ).fetchone()
    
    if existing:
        return existing[0]
    
    # Create VC record
    if vc_data:
        url = vc_data.get('url', '')
        domain = ''
        if url:
            from urllib.parse import urlparse
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
            except:
                pass
        
        portfolio_url = vc_data.get('portfolio_url_pattern') or vc_data.get('portfolio_url') or url
        focus_areas = json.dumps(vc_data.get('focus_areas', []))
        
        conn.execute("""
            INSERT INTO vcs (firm_name, url, domain, type, stage, focus_areas, portfolio_url, 
                           discovered_from, user_added, verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            firm_name,
            url,
            domain,
            vc_data.get('type', 'VC'),
            vc_data.get('stage', 'Unknown'),
            focus_areas,
            portfolio_url,
            'migration',
            False,
            False,
            datetime.now(),
            datetime.now()
        ))
        conn.commit()
        return conn.execute("SELECT id FROM vcs WHERE firm_name = ?", (firm_name,)).fetchone()[0]
    else:
        # Minimal VC record
        conn.execute("""
            INSERT INTO vcs (firm_name, discovered_from, user_added, verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            firm_name,
            'migration',
            False,
            False,
            datetime.now(),
            datetime.now()
        ))
        conn.commit()
        return conn.execute("SELECT id FROM vcs WHERE firm_name = ?", (firm_name,)).fetchone()[0]

def infer_funding_round(yc_batch, last_raise_stage, source):
    """Infer funding round from available data"""
    if last_raise_stage:
        return last_raise_stage
    
    # YC batches are typically Seed stage
    if yc_batch:
        return 'Seed'
    
    # Antler is typically Pre-Seed/Seed
    if source == 'antler':
        return 'Pre-Seed'
    
    return 'Seed'

def migrate_companies(conn):
    """Migrate company.source to company_investments relationships"""
    print("="*70)
    print("MIGRATING COMPANY SOURCES TO INVESTOR RELATIONSHIPS")
    print("="*70)
    
    # Load VC seed data for reference
    seed_file = Path(__file__).parent.parent / "data" / "seed_data.json"
    vc_seed_data = {}
    if seed_file.exists():
        with open(seed_file, 'r') as f:
            seed_data = json.load(f)
            for vc in seed_data.get('vcs', []):
                vc_seed_data[vc['firm_name'].lower()] = vc
    
    # Map source values to VC firm names
    source_to_vc = {
        'yc': 'Y Combinator',
        'y_combinator': 'Y Combinator',
        'antler': 'Antler',
        'github': None,  # Not a VC, skip
        'scanned': None,  # Not a VC, skip
    }
    
    # Get all companies with source values
    companies = conn.execute("""
        SELECT id, name, domain, source, yc_batch, last_raise_stage, 
               last_raise_date, funding_amount, funding_currency
        FROM companies
        WHERE source IS NOT NULL AND source != ''
    """).fetchall()
    
    print(f"\nFound {len(companies)} companies with source values")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for company in companies:
        company_id, name, domain, source, yc_batch, last_raise_stage, last_raise_date, funding_amount, funding_currency = company
        
        # Map source to VC firm name
        vc_firm_name = source_to_vc.get(source.lower())
        
        if not vc_firm_name:
            skipped += 1
            continue
        
        try:
            # Ensure VC exists
            vc_data = vc_seed_data.get(vc_firm_name.lower())
            investor_id = ensure_vc_exists(conn, vc_firm_name, vc_data)
            
            # Check if investment relationship already exists
            existing = conn.execute("""
                SELECT id FROM company_investments 
                WHERE company_id = ? AND investor_id = ?
            """, (company_id, investor_id)).fetchone()
            
            if existing:
                continue  # Already migrated
            
            # Determine investment type
            investment_type = 'accelerator_batch' if source.lower() in ['yc', 'y_combinator', 'antler'] else 'portfolio'
            
            # Infer funding round
            funding_round = infer_funding_round(yc_batch, last_raise_stage, source)
            
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
                funding_amount,
                funding_currency or 'USD',
                last_raise_date,
                datetime.now().date(),
                None,  # valid_to (NULL = active)
                True if investment_type == 'accelerator_batch' else False,  # Lead for accelerators
                datetime.now(),
                datetime.now()
            ))
            
            migrated += 1
            
            if migrated % 100 == 0:
                print(f"  Migrated {migrated} companies...")
                conn.commit()
        
        except Exception as e:
            errors += 1
            print(f"  Error migrating company {company_id} ({name}): {e}")
    
    conn.commit()
    
    print(f"\n{'='*70}")
    print(f"MIGRATION COMPLETE")
    print(f"{'='*70}")
    print(f"Migrated: {migrated} companies")
    print(f"Skipped: {skipped} companies (non-VC sources)")
    print(f"Errors: {errors} companies")
    
    # Show summary
    summary = conn.execute("""
        SELECT 
            v.firm_name,
            COUNT(ci.id) as investment_count
        FROM vcs v
        LEFT JOIN company_investments ci ON v.id = ci.investor_id
        GROUP BY v.firm_name
        ORDER BY investment_count DESC
        LIMIT 10
    """).fetchall()
    
    print(f"\nTop investors by company count:")
    for firm_name, count in summary:
        print(f"  {firm_name}: {count} companies")

if __name__ == "__main__":
    conn = get_db_connection()
    try:
        migrate_companies(conn)
    finally:
        conn.close()

