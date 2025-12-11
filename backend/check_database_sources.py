"""Check what portfolios are in the database"""
import sys
import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    conn = duckdb.connect('celerio_scout.db', read_only=True)
    
    print("=" * 80)
    print("DATABASE PORTFOLIO ANALYSIS")
    print("=" * 80)
    
    # Total companies
    total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    print(f"\nTotal companies: {total}")
    
    # Companies by source
    print("\nCompanies by source:")
    sources = conn.execute("SELECT source, COUNT(*) as cnt FROM companies GROUP BY source ORDER BY cnt DESC").fetchall()
    for source, count in sources:
        print(f"  {source}: {count}")
    
    # YC companies
    yc_query = """
        SELECT COUNT(*) FROM companies 
        WHERE source LIKE '%yc%' 
           OR source LIKE '%Y Combinator%' 
           OR yc_batch IS NOT NULL
    """
    yc_count = conn.execute(yc_query).fetchone()[0]
    print(f"\nYC companies (by source or yc_batch): {yc_count}")
    
    # Antler companies
    antler_query = """
        SELECT COUNT(*) FROM companies 
        WHERE source LIKE '%antler%' 
           OR source LIKE '%Antler%'
    """
    antler_count = conn.execute(antler_query).fetchone()[0]
    print(f"Antler companies: {antler_count}")
    
    # Sample companies from each source
    print("\nSample YC companies:")
    yc_samples = conn.execute("""
        SELECT name, domain, source, yc_batch 
        FROM companies 
        WHERE yc_batch IS NOT NULL 
        LIMIT 5
    """).fetchall()
    for name, domain, source, batch in yc_samples:
        print(f"  {name} ({domain}) - Source: {source}, Batch: {batch}")
    
    print("\nSample Antler companies:")
    antler_samples = conn.execute("""
        SELECT name, domain, source 
        FROM companies 
        WHERE source LIKE '%antler%' OR source LIKE '%Antler%'
        LIMIT 5
    """).fetchall()
    for name, domain, source in antler_samples:
        print(f"  {name} ({domain}) - Source: {source}")
    
    # Data completeness
    print("\nData Completeness:")
    stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(last_raise_stage) as with_stage,
            COUNT(CASE WHEN focus_areas IS NOT NULL AND focus_areas != '' AND focus_areas != '[]' THEN 1 END) as with_focus,
            COUNT(employee_count) as with_employees,
            COUNT(funding_amount) as with_funding
        FROM companies
    """).fetchone()
    
    total, stage, focus, emp, fund = stats
    print(f"  With stage: {stage}/{total} ({stage/total*100:.1f}%)")
    print(f"  With focus areas: {focus}/{total} ({focus/total*100:.1f}%)")
    print(f"  With employees: {emp}/{total} ({emp/total*100:.1f}%)")
    print(f"  With funding: {fund}/{total} ({fund/total*100:.1f}%)")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

