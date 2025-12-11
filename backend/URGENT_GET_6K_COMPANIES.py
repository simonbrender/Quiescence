"""
URGENT: Get 6K+ Companies from YC + Antler
This script MUST be run when backend is STOPPED
It will scrape ALL companies with NO LIMITS
"""
import asyncio
import sys
import duckdb
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*80)
print("URGENT: GETTING 6K+ COMPANIES FROM YC + ANTLER")
print("="*80)
print("\nCRITICAL: Backend server MUST be stopped!")
print("Press Ctrl+C NOW if backend is running, then restart this script\n")
time.sleep(3)

async def get_6k_companies():
    """Get 6k+ companies from YC and Antler"""
    
    # Connect to database
    print("Connecting to database...")
    conn = None
    for attempt in range(5):
        try:
            conn = duckdb.connect("celerio_scout.db", read_only=False)
            print("Connected!\n")
            break
        except Exception as e:
            if attempt < 4:
                print(f"Database locked (attempt {attempt+1}/5), waiting...")
                time.sleep(5)
            else:
                print("ERROR: Database still locked. STOP BACKEND SERVER!")
                return
    
    if not conn:
        return
    
    try:
        # Get initial counts
        initial_yc = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'yc'").fetchone()[0]
        initial_antler = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'antler'").fetchone()[0]
        
        print(f"Current: YC={initial_yc}, Antler={initial_antler}, Total={initial_yc + initial_antler}\n")
        
        # STEP 1: YC - Use comprehensive scraper
        print("="*80)
        print("STEP 1: YC COMPREHENSIVE (Target: 4,000 companies)")
        print("="*80)
        
        try:
            from comprehensive_portfolio_scraper_v2 import ComprehensivePortfolioScraper
            
            scraper = ComprehensivePortfolioScraper()
            print("Scraping ALL 40 YC batches (2005-2025)...")
            yc_companies = await scraper.scrape_yc_comprehensive()
            print(f"Found {len(yc_companies)} YC companies")
            
            # Save ALL companies
            saved_yc = 0
            for company in yc_companies:
                try:
                    domain = company.get('domain', '').strip()
                    name = company.get('name', '').strip()
                    if not domain and not name:
                        continue
                    
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
                        """, (name, domain, 'yc', company.get('yc_batch'), focus_areas_json))
                        saved_yc += 1
                except:
                    continue
            
            conn.commit()
            print(f"Saved {saved_yc} new YC companies")
            await scraper.close_session()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # STEP 2: Antler - Use comprehensive scraper
        print("\n" + "="*80)
        print("STEP 2: ANTLER COMPREHENSIVE (Target: 1,000+ companies)")
        print("="*80)
        
        try:
            scraper = ComprehensivePortfolioScraper()
            print("Scraping Antler with infinite scroll...")
            antler_companies = await scraper.scrape_antler_comprehensive()
            print(f"Found {len(antler_companies)} Antler companies")
            
            # Save ALL companies
            saved_antler = 0
            for company in antler_companies:
                try:
                    domain = company.get('domain', '').strip()
                    name = company.get('name', '').strip()
                    if not domain and not name:
                        continue
                    
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
                        """, (name, domain, 'antler', focus_areas_json))
                        saved_antler += 1
                except:
                    continue
            
            conn.commit()
            print(f"Saved {saved_antler} new Antler companies")
            await scraper.close_session()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Final counts
        final_yc = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'yc'").fetchone()[0]
        final_antler = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'antler'").fetchone()[0]
        total = final_yc + final_antler
        
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"YC: {final_yc} (added {final_yc - initial_yc})")
        print(f"Antler: {final_antler} (added {final_antler - initial_antler})")
        print(f"TOTAL: {total}")
        
        if total >= 5000:
            print("\nSUCCESS: Target met!")
        else:
            print(f"\nWARNING: Only {total}, need 6k+")
        
        print("="*80 + "\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(get_6k_companies())

