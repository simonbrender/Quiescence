"""
Monitor Workflow Progress - Check status of running workflows
"""
import duckdb
import json
import sys
from pathlib import Path

def monitor_progress():
    """Monitor workflow progress by checking database"""
    
    print("\n" + "="*80)
    print("WORKFLOW PROGRESS MONITOR")
    print("="*80 + "\n")
    
    try:
        # Try to connect (read-only)
        conn = duckdb.connect("celerio_scout.db", read_only=True)
        
        # Get current counts
        companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        vcs = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
        relationships = conn.execute("SELECT COUNT(*) FROM company_investments").fetchone()[0]
        
        # Get breakdown by source
        yc_companies = conn.execute(
            "SELECT COUNT(*) FROM companies WHERE source = 'yc'"
        ).fetchone()[0]
        
        antler_companies = conn.execute(
            "SELECT COUNT(*) FROM companies WHERE source = 'antler'"
        ).fetchone()[0]
        
        other_companies = conn.execute(
            "SELECT COUNT(*) FROM companies WHERE source NOT IN ('yc', 'antler') OR source IS NULL"
        ).fetchone()[0]
        
        # Get VC types
        vc_types = conn.execute("""
            SELECT type, COUNT(*) as count
            FROM vcs
            GROUP BY type
        """).fetchall()
        
        print("Current Database State:")
        print(f"  Companies: {companies}")
        print(f"    - YC: {yc_companies}")
        print(f"    - Antler: {antler_companies}")
        print(f"    - Other: {other_companies}")
        print(f"\n  VCs: {vcs}")
        for vc_type, count in vc_types:
            print(f"    - {vc_type or 'Unknown'}: {count}")
        print(f"\n  Relationships: {relationships}")
        
        # Check if workflow results file exists
        results_file = Path("workflow_results.json")
        if results_file.exists():
            print("\n" + "-"*80)
            print("Workflow Results Found:")
            print("-"*80)
            with open(results_file, 'r') as f:
                results = json.load(f)
                print(f"  YC Companies: {results.get('yc_companies', 0)}")
                print(f"  Antler Companies: {results.get('antler_companies', 0)}")
                print(f"  VC Portfolio Companies: {results.get('vc_companies', 0)}")
                print(f"  Discovered VCs: {results.get('discovered_vcs', 0)}")
                print(f"  Relationships Created: {results.get('relationships_created', 0)}")
                
                if results.get('errors'):
                    print(f"\n  Errors: {len(results['errors'])}")
                    for error in results['errors'][:5]:  # Show first 5
                        print(f"    - {error}")
        else:
            print("\n  Workflow still running... (no results file yet)")
        
        # Progress estimates
        print("\n" + "-"*80)
        print("Progress Estimates:")
        print("-"*80)
        
        yc_target = 4000
        antler_target = 1000
        
        if yc_companies > 0:
            yc_pct = min(100, (yc_companies / yc_target) * 100)
            print(f"  YC Scraping: {yc_pct:.1f}% ({yc_companies}/{yc_target})")
        else:
            print(f"  YC Scraping: Not started yet")
        
        if antler_companies > 0:
            antler_pct = min(100, (antler_companies / antler_target) * 100)
            print(f"  Antler Scraping: {antler_pct:.1f}% ({antler_companies}/{antler_target})")
        else:
            print(f"  Antler Scraping: Not started yet")
        
        conn.close()
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"Error monitoring progress: {e}")
        print("Database may be locked or workflow not started yet")

if __name__ == "__main__":
    monitor_progress()

