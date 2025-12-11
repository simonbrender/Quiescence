"""
Force Comprehensive Scraping - Get 6k+ from YC+Antler and ALL VCs
This script will actually execute the scraping NOW
"""
import asyncio
import sys
import duckdb
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*80)
print("FORCING COMPREHENSIVE SCRAPING - 6K+ COMPANIES")
print("="*80 + "\n")

async def force_comprehensive_scraping():
    """Force comprehensive scraping to get 6k+ companies"""
    
    # Wait for database to be available
    print("Waiting for database to be available...")
    conn = None
    for attempt in range(10):
        try:
            conn = duckdb.connect("celerio_scout.db", read_only=False)
            print("Database connected!\n")
            break
        except Exception as e:
            if attempt < 9:
                print(f"Attempt {attempt + 1}/10: Database locked, waiting 10 seconds...")
                time.sleep(10)
            else:
                print("ERROR: Could not access database after 10 attempts")
                print("Please stop the backend server and try again")
                return
    
    if not conn:
        return
    
    try:
        # Get initial counts
        initial_yc = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'yc'").fetchone()[0]
        initial_antler = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'antler'").fetchone()[0]
        initial_total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        
        print(f"Initial State:")
        print(f"  YC: {initial_yc}")
        print(f"  Antler: {initial_antler}")
        print(f"  Total: {initial_total}\n")
        
        # STEP 1: YC Comprehensive Scraping
        print("="*80)
        print("STEP 1: YC COMPREHENSIVE SCRAPING")
        print("Target: ~4,000 companies from ALL batches")
        print("="*80 + "\n")
        
        try:
            from comprehensive_portfolio_scraper_v2 import ComprehensivePortfolioScraper
            
            scraper = ComprehensivePortfolioScraper()
            print("Starting YC comprehensive scraping...")
            print("This will scrape ALL 40 batches (2005-2025)...")
            print("This may take 30-60 minutes...\n")
            
            yc_companies = await scraper.scrape_yc_comprehensive()
            print(f"\nFound {len(yc_companies)} YC companies")
            
            # Save to database
            if yc_companies:
                print("Saving to database...")
                saved = 0
                for idx, company in enumerate(yc_companies):
                    if idx % 100 == 0 and idx > 0:
                        print(f"  Saved {idx}/{len(yc_companies)}...")
                    
                    try:
                        domain = company.get('domain', '').strip()
                        name = company.get('name', '').strip()
                        
                        if not domain and not name:
                            continue
                        
                        # Check if exists
                        existing = conn.execute(
                            "SELECT id FROM companies WHERE domain = ? OR name = ?",
                            (domain, name)
                        ).fetchone()
                        
                        if not existing:
                            focus_areas = company.get('focus_areas', [])
                            focus_areas_json = json.dumps(focus_areas) if focus_areas else None
                            
                            conn.execute("""
                                INSERT INTO companies 
                                (name, domain, source, yc_batch, focus_areas, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """, (
                                name,
                                domain,
                                'yc',
                                company.get('yc_batch'),
                                focus_areas_json
                            ))
                            saved += 1
                    except Exception as e:
                        continue
                
                conn.commit()
                print(f"Saved {saved} new YC companies to database")
            
            await scraper.close_session()
            
        except Exception as e:
            print(f"ERROR in YC scraping: {e}")
            import traceback
            traceback.print_exc()
        
        # STEP 2: Antler Comprehensive Scraping
        print("\n" + "="*80)
        print("STEP 2: ANTLER COMPREHENSIVE SCRAPING")
        print("Target: ~1,000+ companies")
        print("="*80 + "\n")
        
        try:
            scraper = ComprehensivePortfolioScraper()
            print("Starting Antler comprehensive scraping...")
            print("This will use infinite scroll to get ALL companies...")
            print("This may take 10-20 minutes...\n")
            
            antler_companies = await scraper.scrape_antler_comprehensive()
            print(f"\nFound {len(antler_companies)} Antler companies")
            
            # Save to database
            if antler_companies:
                print("Saving to database...")
                saved = 0
                for idx, company in enumerate(antler_companies):
                    if idx % 50 == 0 and idx > 0:
                        print(f"  Saved {idx}/{len(antler_companies)}...")
                    
                    try:
                        domain = company.get('domain', '').strip()
                        name = company.get('name', '').strip()
                        
                        if not domain and not name:
                            continue
                        
                        # Check if exists
                        existing = conn.execute(
                            "SELECT id FROM companies WHERE domain = ? OR name = ?",
                            (domain, name)
                        ).fetchone()
                        
                        if not existing:
                            focus_areas = company.get('focus_areas', [])
                            focus_areas_json = json.dumps(focus_areas) if focus_areas else None
                            
                            conn.execute("""
                                INSERT INTO companies 
                                (name, domain, source, focus_areas, created_at, updated_at)
                                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """, (
                                name,
                                domain,
                                'antler',
                                focus_areas_json
                            ))
                            saved += 1
                    except Exception as e:
                        continue
                
                conn.commit()
                print(f"Saved {saved} new Antler companies to database")
            
            await scraper.close_session()
            
        except Exception as e:
            print(f"ERROR in Antler scraping: {e}")
            import traceback
            traceback.print_exc()
        
        # STEP 3: Scrape ALL VCs
        print("\n" + "="*80)
        print("STEP 3: SCRAPE ALL VCs, STUDIOS, ACCELERATORS")
        print("="*80 + "\n")
        
        try:
            from scale_all_vcs import scrape_all_vcs_comprehensive
            
            print("Getting all VCs from database...")
            vc_results = await scrape_all_vcs_comprehensive(conn)
            print(f"\nScraped {vc_results.get('total_companies', 0)} companies from all VCs")
            
        except Exception as e:
            print(f"ERROR in VC scraping: {e}")
            import traceback
            traceback.print_exc()
        
        # Final counts
        final_yc = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'yc'").fetchone()[0]
        final_antler = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'antler'").fetchone()[0]
        final_total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        
        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)
        print(f"\nYC Companies:")
        print(f"  Before: {initial_yc}")
        print(f"  After: {final_yc}")
        print(f"  Added: {final_yc - initial_yc}")
        
        print(f"\nAntler Companies:")
        print(f"  Before: {initial_antler}")
        print(f"  After: {final_antler}")
        print(f"  Added: {final_antler - initial_antler}")
        
        print(f"\nTotal Companies:")
        print(f"  Before: {initial_total}")
        print(f"  After: {final_total}")
        print(f"  Added: {final_total - initial_total}")
        
        yc_antler_total = final_yc + final_antler
        print(f"\nYC + Antler Total: {yc_antler_total}")
        
        if yc_antler_total >= 5000:
            print("SUCCESS: Target of 5k+ companies met!")
        else:
            print(f"WARNING: Only {yc_antler_total} companies, target was 6k+")
        
        print("\n" + "="*80 + "\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("WARNING: This will take 1-2 hours to complete")
    print("Make sure backend server is STOPPED before running")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to start...")
    time.sleep(5)
    
    asyncio.run(force_comprehensive_scraping())



