"""
Execute Full Workflows - Direct Database Access
Runs comprehensive scraping and discovery, populates database with real data
"""
import asyncio
import sys
import duckdb
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*80)
print("EXECUTING FULL WORKFLOWS - COMPREHENSIVE DATA POPULATION")
print("="*80 + "\n")

async def execute_full_workflows():
    """Execute all workflows to populate system with real data"""
    
    results = {
        'yc_companies': 0,
        'antler_companies': 0,
        'vc_companies': 0,
        'discovered_vcs': 0,
        'relationships_created': 0,
        'total_companies': 0,
        'total_vcs': 0,
        'total_relationships': 0,
        'errors': []
    }
    
    # Try to connect to database (with retry logic)
    conn = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"[Attempt {attempt + 1}/{max_retries}] Connecting to database...")
            conn = duckdb.connect("celerio_scout.db", read_only=False)
            print("   Database connected successfully\n")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   Database locked, waiting 5 seconds... ({e})")
                time.sleep(5)
            else:
                print(f"   ERROR: Could not connect to database after {max_retries} attempts")
                print("   Make sure no other process is using the database")
                return results
    
    if not conn:
        return results
    
    try:
        # Get initial counts
        print("[1/6] Getting initial statistics...")
        initial_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        initial_vcs = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
        initial_relationships = conn.execute("SELECT COUNT(*) FROM company_investments").fetchone()[0]
        
        print(f"   Companies: {initial_companies}")
        print(f"   VCs: {initial_vcs}")
        print(f"   Relationships: {initial_relationships}\n")
        
        # Workflow 1: YC Comprehensive Scraping
        print("="*80)
        print("[2/6] WORKFLOW 1: YC Comprehensive Scraping")
        print("="*80)
        print("   Scraping ALL YC batches (2005-2025)...")
        print("   Expected: ~4,000 companies\n")
        
        try:
            from comprehensive_portfolio_scraper_v2 import ComprehensivePortfolioScraper
            
            scraper = ComprehensivePortfolioScraper()
            yc_companies = await scraper.scrape_yc_comprehensive()
            print(f"\n   Found {len(yc_companies)} YC companies")
            
            # Save to database
            if yc_companies:
                saved = await save_companies_to_db(conn, yc_companies, 'yc')
                results['yc_companies'] = saved
                print(f"   Saved {saved} YC companies to database")
            
            await scraper.close_session()
            
        except Exception as e:
            error_msg = f"YC scraping error: {str(e)}"
            print(f"   ERROR: {error_msg}")
            results['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
        
        # Workflow 2: Antler Comprehensive Scraping
        print("\n" + "="*80)
        print("[3/6] WORKFLOW 2: Antler Comprehensive Scraping")
        print("="*80)
        print("   Scraping Antler portfolio with infinite scroll...")
        print("   Expected: ~1,000 companies\n")
        
        try:
            scraper = ComprehensivePortfolioScraper()
            antler_companies = await scraper.scrape_antler_comprehensive()
            print(f"\n   Found {len(antler_companies)} Antler companies")
            
            # Save to database
            if antler_companies:
                saved = await save_companies_to_db(conn, antler_companies, 'antler')
                results['antler_companies'] = saved
                print(f"   Saved {saved} Antler companies to database")
            
            await scraper.close_session()
            
        except Exception as e:
            error_msg = f"Antler scraping error: {str(e)}"
            print(f"   ERROR: {error_msg}")
            results['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
        
        # Workflow 3: VC Discovery (skip if timing out - use existing VCs)
        print("\n" + "="*80)
        print("[4/6] WORKFLOW 3: VC Auto-Discovery")
        print("="*80)
        print("   Discovering VCs from multiple sources...")
        print("   Note: This may take time due to web scraping\n")
        
        try:
            from enhanced_vc_discovery import EnhancedVCDiscovery
            
            discovery = EnhancedVCDiscovery()
            discovered_vcs = await discovery.discover_all_comprehensive()
            print(f"\n   Discovered {len(discovered_vcs)} VCs")
            
            # Save to database
            if discovered_vcs:
                saved = await save_vcs_to_db(conn, discovered_vcs)
                results['discovered_vcs'] = saved
                print(f"   Saved {saved} new VCs to database")
            else:
                print("   No new VCs discovered (may have timed out)")
            
            await discovery.close_session()
            
        except Exception as e:
            error_msg = f"VC discovery error: {str(e)}"
            print(f"   ERROR: {error_msg}")
            results['errors'].append(error_msg)
            print("   Continuing with existing VCs...")
        
        # Workflow 4: Scrape All VCs
        print("\n" + "="*80)
        print("[5/6] WORKFLOW 4: Scrape All VCs")
        print("="*80)
        
        try:
            from scale_all_vcs import scrape_all_vcs_comprehensive
            
            vc_results = await scrape_all_vcs_comprehensive(conn)
            results['vc_companies'] = vc_results.get('total_companies', 0)
            print(f"\n   Scraped {results['vc_companies']} companies from all VCs")
            
        except Exception as e:
            error_msg = f"All VCs scraping error: {str(e)}"
            print(f"   ERROR: {error_msg}")
            results['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
        
        # Workflow 5: Create Relationships
        print("\n" + "="*80)
        print("[6/6] WORKFLOW 5: Create Investor-Company Relationships")
        print("="*80)
        
        try:
            relationships_created = await create_relationships(conn)
            results['relationships_created'] = relationships_created
            print(f"\n   Created {relationships_created} investor-company relationships")
            
        except Exception as e:
            error_msg = f"Relationship creation error: {str(e)}"
            print(f"   ERROR: {error_msg}")
            results['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
        
        # Final counts
        final_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        final_vcs = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
        final_relationships = conn.execute("SELECT COUNT(*) FROM company_investments").fetchone()[0]
        
        results['total_companies'] = final_companies
        results['total_vcs'] = final_vcs
        results['total_relationships'] = final_relationships
        
        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)
        print(f"\nCompanies:")
        print(f"  Initial: {initial_companies}")
        print(f"  Final: {final_companies}")
        print(f"  Added: {final_companies - initial_companies}")
        print(f"\nVCs:")
        print(f"  Initial: {initial_vcs}")
        print(f"  Final: {final_vcs}")
        print(f"  Added: {final_vcs - initial_vcs}")
        print(f"\nRelationships:")
        print(f"  Initial: {initial_relationships}")
        print(f"  Final: {final_relationships}")
        print(f"  Added: {final_relationships - initial_relationships}")
        
        print(f"\nWorkflow Breakdown:")
        print(f"  YC Companies: {results['yc_companies']}")
        print(f"  Antler Companies: {results['antler_companies']}")
        print(f"  VC Portfolio Companies: {results['vc_companies']}")
        print(f"  Discovered VCs: {results['discovered_vcs']}")
        print(f"  Relationships Created: {results['relationships_created']}")
        
        if results['errors']:
            print(f"\nErrors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        print("\n" + "="*80)
        print("WORKFLOWS COMPLETE")
        print("="*80 + "\n")
        
    finally:
        conn.close()
    
    return results

async def save_companies_to_db(conn, companies: List[Dict], source: str) -> int:
    """Save companies to database"""
    saved = 0
    skipped = 0
    
    for idx, company in enumerate(companies):
        if idx % 100 == 0 and idx > 0:
            print(f"     Saving companies... {idx}/{len(companies)}")
        
        try:
            domain = company.get('domain', '').strip()
            name = company.get('name', '').strip()
            
            if not domain and not name:
                skipped += 1
                continue
            
            # Check if company exists
            existing = conn.execute(
                "SELECT id FROM companies WHERE domain = ? OR name = ?",
                (domain, name)
            ).fetchone()
            
            if existing:
                # Update existing
                conn.execute("""
                    UPDATE companies 
                    SET source = COALESCE(?, source), 
                        yc_batch = COALESCE(?, yc_batch),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (source, company.get('yc_batch'), existing[0]))
            else:
                # Insert new
                focus_areas = company.get('focus_areas', [])
                focus_areas_json = json.dumps(focus_areas) if focus_areas else None
                
                conn.execute("""
                    INSERT INTO companies 
                    (name, domain, source, yc_batch, focus_areas, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    name,
                    domain,
                    source,
                    company.get('yc_batch'),
                    focus_areas_json
                ))
                saved += 1
        except Exception as e:
            skipped += 1
            continue
    
    conn.commit()
    if skipped > 0:
        print(f"     Skipped {skipped} companies (duplicates or errors)")
    return saved

async def save_vcs_to_db(conn, vcs: List[Dict]) -> int:
    """Save discovered VCs to database"""
    saved = 0
    
    for vc in vcs:
        try:
            firm_name = vc.get('firm_name', '').strip()
            if not firm_name:
                continue
            
            # Check if VC exists
            existing = conn.execute(
                "SELECT id FROM vcs WHERE firm_name = ?",
                (firm_name,)
            ).fetchone()
            
            if not existing:
                focus_areas = vc.get('focus_areas', [])
                focus_areas_json = json.dumps(focus_areas) if focus_areas else None
                
                vc_id = abs(hash(firm_name)) % 1000000
                conn.execute("""
                    INSERT INTO vcs 
                    (id, firm_name, url, domain, type, stage, focus_areas, portfolio_url, 
                     discovered_from, user_added, verified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    vc_id,
                    firm_name,
                    vc.get('url'),
                    vc.get('domain'),
                    vc.get('type', 'VC'),
                    vc.get('stage', 'Unknown'),
                    focus_areas_json,
                    vc.get('portfolio_url'),
                    vc.get('discovered_from', ''),
                    False,
                    False
                ))
                saved += 1
        except Exception as e:
            continue
    
    conn.commit()
    return saved

async def create_relationships(conn) -> int:
    """Create investor-company relationships from source data"""
    created = 0
    
    # Get all companies with source
    companies = conn.execute("""
        SELECT id, domain, name, source, yc_batch
        FROM companies
        WHERE source IS NOT NULL AND source != ''
    """).fetchall()
    
    # Get VC mappings
    vc_mappings = {
        'yc': 'Y Combinator',
        'antler': 'Antler'
    }
    
    for company in companies:
        company_id, domain, name, source, yc_batch = company
        
        # Find investor ID
        investor_name = vc_mappings.get(source.lower())
        if not investor_name:
            continue
        
        investor = conn.execute(
            "SELECT id FROM vcs WHERE firm_name LIKE ?",
            (f"%{investor_name}%",)
        ).fetchone()
        
        if not investor:
            continue
        
        investor_id = investor[0]
        
        # Check if relationship exists
        existing = conn.execute("""
            SELECT id FROM company_investments
            WHERE company_id = ? AND investor_id = ?
        """, (company_id, investor_id)).fetchone()
        
        if not existing:
            # Create relationship
            conn.execute("""
                INSERT INTO company_investments
                (company_id, investor_id, investment_type, funding_round, 
                 investment_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                company_id,
                investor_id,
                'Portfolio Company',
                yc_batch if yc_batch else 'Seed',
                datetime.now().date()
            ))
            created += 1
    
    conn.commit()
    return created

if __name__ == "__main__":
    print("Starting full workflow execution...")
    print("This will:")
    print("  1. Scrape ALL YC batches (~4k companies)")
    print("  2. Scrape Antler portfolio (~1k companies)")
    print("  3. Discover new VCs")
    print("  4. Scrape all VC portfolios")
    print("  5. Create investor-company relationships")
    print("\nThis may take a while. Please be patient...\n")
    
    results = asyncio.run(execute_full_workflows())
    
    # Save results
    with open("workflow_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to workflow_results.json")

