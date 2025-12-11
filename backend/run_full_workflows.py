"""
Run Full Workflows - Comprehensive Data Population
Triggers all scraping, discovery, and relationship creation workflows
"""
import asyncio
import sys
import duckdb
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*80)
print("FULL WORKFLOW EXECUTION - COMPREHENSIVE DATA POPULATION")
print("="*80 + "\n")

async def run_full_workflows():
    """Run all workflows to populate the system with real data"""
    
    results = {
        'yc_companies': 0,
        'antler_companies': 0,
        'vc_companies': 0,
        'discovered_vcs': 0,
        'total_companies': 0,
        'total_relationships': 0,
        'errors': []
    }
    
    try:
        # Connect to database
        print("[1/5] Connecting to database...")
        conn = duckdb.connect("celerio_scout.db")
        print("   Database connected\n")
        
        # Get initial counts
        initial_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        initial_vcs = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
        initial_relationships = conn.execute("SELECT COUNT(*) FROM company_investments").fetchone()[0]
        
        print(f"Initial State:")
        print(f"  Companies: {initial_companies}")
        print(f"  VCs: {initial_vcs}")
        print(f"  Relationships: {initial_relationships}\n")
        
        # Workflow 1: Comprehensive YC Scraping
        print("="*80)
        print("[2/5] WORKFLOW 1: YC Comprehensive Scraping")
        print("="*80)
        try:
            from comprehensive_portfolio_scraper_v2 import ComprehensivePortfolioScraper
            
            scraper = ComprehensivePortfolioScraper()
            yc_companies = await scraper.scrape_yc_comprehensive()
            results['yc_companies'] = len(yc_companies)
            
            # Save YC companies to database
            if yc_companies:
                print(f"\nSaving {len(yc_companies)} YC companies to database...")
                saved_count = await save_companies_to_db(conn, yc_companies, 'yc')
                print(f"Saved {saved_count} YC companies")
                results['yc_companies'] = saved_count
            
            await scraper.close_session()
            
        except Exception as e:
            error_msg = f"YC scraping error: {str(e)}"
            print(f"ERROR: {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 2: Comprehensive Antler Scraping
        print("\n" + "="*80)
        print("[3/5] WORKFLOW 2: Antler Comprehensive Scraping")
        print("="*80)
        try:
            scraper = ComprehensivePortfolioScraper()
            antler_companies = await scraper.scrape_antler_comprehensive()
            results['antler_companies'] = len(antler_companies)
            
            # Save Antler companies to database
            if antler_companies:
                print(f"\nSaving {len(antler_companies)} Antler companies to database...")
                saved_count = await save_companies_to_db(conn, antler_companies, 'antler')
                print(f"Saved {saved_count} Antler companies")
                results['antler_companies'] = saved_count
            
            await scraper.close_session()
            
        except Exception as e:
            error_msg = f"Antler scraping error: {str(e)}"
            print(f"ERROR: {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 3: VC Discovery
        print("\n" + "="*80)
        print("[4/5] WORKFLOW 3: VC Auto-Discovery")
        print("="*80)
        try:
            from enhanced_vc_discovery import EnhancedVCDiscovery
            
            discovery = EnhancedVCDiscovery()
            discovered_vcs = await discovery.discover_all_comprehensive()
            results['discovered_vcs'] = len(discovered_vcs)
            
            # Save discovered VCs to database
            if discovered_vcs:
                print(f"\nSaving {len(discovered_vcs)} discovered VCs to database...")
                saved_count = await save_vcs_to_db(conn, discovered_vcs)
                print(f"Saved {saved_count} new VCs")
                results['discovered_vcs'] = saved_count
            
            await discovery.close_session()
            
        except Exception as e:
            error_msg = f"VC discovery error: {str(e)}"
            print(f"ERROR: {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 4: All VCs Portfolio Scraping
        print("\n" + "="*80)
        print("[5/5] WORKFLOW 4: All VCs Portfolio Scraping")
        print("="*80)
        try:
            from scale_all_vcs import scrape_all_vcs_comprehensive
            
            vc_results = await scrape_all_vcs_comprehensive(conn)
            results['vc_companies'] = vc_results.get('total_companies', 0)
            print(f"\nScraped {results['vc_companies']} companies from all VCs")
            
        except Exception as e:
            error_msg = f"All VCs scraping error: {str(e)}"
            print(f"ERROR: {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 5: Create Relationships
        print("\n" + "="*80)
        print("[BONUS] Creating Investor-Company Relationships")
        print("="*80)
        try:
            relationships_created = await create_relationships(conn)
            results['total_relationships'] = relationships_created
            print(f"Created {relationships_created} investor-company relationships")
            
        except Exception as e:
            error_msg = f"Relationship creation error: {str(e)}"
            print(f"ERROR: {error_msg}")
            results['errors'].append(error_msg)
        
        # Final counts
        final_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        final_vcs = conn.execute("SELECT COUNT(*) FROM vcs").fetchone()[0]
        final_relationships = conn.execute("SELECT COUNT(*) FROM company_investments").fetchone()[0]
        
        results['total_companies'] = final_companies
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
        
        if results['errors']:
            print(f"\nErrors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("WORKFLOWS COMPLETE")
        print("="*80 + "\n")
        
        return results
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return results

async def save_companies_to_db(conn, companies: List[Dict], source: str) -> int:
    """Save companies to database"""
    saved = 0
    for company in companies:
        try:
            domain = company.get('domain', '').strip()
            name = company.get('name', '').strip()
            
            if not domain and not name:
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
                    SET source = ?, yc_batch = ?, updated_at = CURRENT_TIMESTAMP
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
            print(f"  Error saving company {company.get('name', 'unknown')}: {e}")
            continue
    
    conn.commit()
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
            print(f"  Error saving VC {vc.get('firm_name', 'unknown')}: {e}")
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
            "SELECT id FROM vcs WHERE firm_name = ?",
            (investor_name,)
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
    results = asyncio.run(run_full_workflows())
    
    # Save results to file
    with open("workflow_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to workflow_results.json")



