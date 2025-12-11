"""
Show Data Location - Display where all data is stored and how to access it
"""
import duckdb
import json
import os
from pathlib import Path

def show_data_location():
    """Show where all data is stored"""
    
    print("\n" + "="*80)
    print("DATA LOCATION GUIDE")
    print("="*80 + "\n")
    
    # Database location
    db_path = Path("celerio_scout.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"[OK] DATABASE: {db_path.absolute()}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Format: DuckDB")
        
        # Try to read database (read-only)
        try:
            conn = duckdb.connect(str(db_path), read_only=True)
            
            # Get table counts
            companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
            vcs = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
            relationships = conn.execute("SELECT COUNT(*) FROM company_investments").fetchone()[0]
            
            print(f"\n  Current Data:")
            print(f"    Companies: {companies}")
            print(f"    VCs: {vcs}")
            print(f"    Relationships: {relationships}")
            
            # Show breakdown
            if companies > 0:
                yc = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'yc'").fetchone()[0]
                antler = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'antler'").fetchone()[0]
                print(f"\n    By Source:")
                print(f"      YC: {yc}")
                print(f"      Antler: {antler}")
                print(f"      Other: {companies - yc - antler}")
            
            conn.close()
            
        except Exception as e:
            print(f"  [WARN] Could not read database: {e}")
            print("  (Database may be locked by another process)")
    else:
        print(f"[NOT FOUND] DATABASE: Not found at {db_path.absolute()}")
    
    # CSV exports
    print(f"\n" + "-"*80)
    print("CSV EXPORTS:")
    print("-"*80)
    
    csv_locations = [
        Path("companies_export.csv"),
        Path("backend/companies_export.csv"),
        Path("../companies_export.csv"),
    ]
    
    found_csvs = []
    for csv_path in csv_locations:
        if csv_path.exists():
            size_kb = csv_path.stat().st_size / 1024
            print(f"[OK] {csv_path.absolute()}")
            print(f"  Size: {size_kb:.2f} KB")
            found_csvs.append(csv_path)
    
    if not found_csvs:
        print("  No CSV exports found")
        print("  To create: Run export_companies.py or use Export button in UI")
    
    # JSON exports
    print(f"\n" + "-"*80)
    print("JSON EXPORTS:")
    print("-"*80)
    
    json_files = [
        "workflow_results.json",
        "workflow_results_api.json",
    ]
    
    found_jsons = []
    for json_file in json_files:
        json_path = Path(json_file)
        if json_path.exists():
            size_kb = json_path.stat().st_size / 1024
            print(f"[OK] {json_path.absolute()}")
            print(f"  Size: {size_kb:.2f} KB")
            found_jsons.append(json_path)
    
    if not found_jsons:
        print("  No workflow results found")
    
    # API access
    print(f"\n" + "-"*80)
    print("API ACCESS:")
    print("-"*80)
    print("  Base URL: http://localhost:8000")
    print("\n  Endpoints:")
    print("    GET  /companies              - Get all companies")
    print("    GET  /companies/export       - Export all companies (JSON)")
    print("    GET  /investors              - Get all investors")
    print("    GET  /investors/relationships - Get all relationships")
    print("    GET  /stats                  - Get statistics")
    print("    POST /portfolios/scrape      - Scrape portfolios")
    print("    POST /portfolios/discover    - Discover VCs")
    
    # How to access
    print(f"\n" + "="*80)
    print("HOW TO ACCESS DATA")
    print("="*80)
    
    print("\n1. DATABASE (DuckDB):")
    print("   Python:")
    print("     import duckdb")
    print("     conn = duckdb.connect('backend/celerio_scout.db', read_only=True)")
    print("     companies = conn.execute('SELECT * FROM companies').fetchall()")
    
    print("\n2. CSV EXPORT:")
    print("   - Use Export button in UI")
    print("   - Or run: python backend/export_companies.py")
    print("   - File: companies_export.csv")
    
    print("\n3. API:")
    print("   curl http://localhost:8000/companies")
    print("   curl http://localhost:8000/investors")
    print("   curl http://localhost:8000/investors/relationships")
    
    print("\n4. UI:")
    print("   - Companies: http://localhost:5173")
    print("   - Graph View: Click 'Graph View' button")
    print("   - Portfolio Scraper: Click 'Portfolio' button")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    show_data_location()

