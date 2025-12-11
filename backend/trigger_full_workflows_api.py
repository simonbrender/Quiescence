"""
Trigger Full Workflows via API - Works with running backend
Triggers all scraping, discovery, and relationship creation via API endpoints
"""
import requests
import json
import time
from typing import Dict

API_BASE = "http://localhost:8000"

def trigger_full_workflows():
    """Trigger all workflows via API"""
    
    print("\n" + "="*80)
    print("FULL WORKFLOW EXECUTION VIA API - COMPREHENSIVE DATA POPULATION")
    print("="*80 + "\n")
    
    results = {
        'initial_stats': {},
        'yc_antler_scraping': {},
        'vc_discovery': {},
        'all_vcs_scraping': {},
        'relationships': {},
        'final_stats': {},
        'errors': []
    }
    
    try:
        # Get initial stats
        print("[1/6] Getting initial statistics...")
        try:
            stats_response = requests.get(f"{API_BASE}/stats", timeout=10)
            if stats_response.status_code == 200:
                results['initial_stats'] = stats_response.json()
                print(f"   Companies: {results['initial_stats'].get('total_companies', 0)}")
                print(f"   VCs: {results['initial_stats'].get('total_vcs', 0)}")
            else:
                print(f"   Warning: Could not get stats (status {stats_response.status_code})")
        except Exception as e:
            print(f"   Warning: Could not connect to API: {e}")
            print("   Make sure backend is running on http://localhost:8000")
            return results
        
        # Workflow 1: Trigger YC + Antler Comprehensive Scraping
        print("\n" + "="*80)
        print("[2/6] WORKFLOW 1: YC + Antler Comprehensive Scraping")
        print("="*80)
        print("   Triggering comprehensive YC and Antler scraping...")
        print("   This will scrape ALL YC batches and Antler portfolio")
        print("   Expected: ~6,000 companies")
        
        try:
            # Check if there's a comprehensive scraping endpoint
            # If not, we'll trigger individual VC scraping
            yc_vc = None
            antler_vc = None
            
            # Get VCs to find YC and Antler IDs
            vcs_response = requests.get(f"{API_BASE}/investors", timeout=10)
            if vcs_response.status_code == 200:
                vcs = vcs_response.json()
                for vc in vcs:
                    firm_name = vc.get('firm_name', '').lower()
                    if 'y combinator' in firm_name or 'yc' in firm_name:
                        yc_vc = vc
                    elif 'antler' in firm_name:
                        antler_vc = vc
                
                print(f"   Found YC: {yc_vc['firm_name'] if yc_vc else 'Not found'}")
                print(f"   Found Antler: {antler_vc['firm_name'] if antler_vc else 'Not found'}")
            
            # Trigger scraping for YC and Antler
            if yc_vc or antler_vc:
                vcs_to_scrape = []
                if yc_vc:
                    vcs_to_scrape.append(yc_vc['id'])
                if antler_vc:
                    vcs_to_scrape.append(antler_vc['id'])
                
                if vcs_to_scrape:
                    print(f"\n   Triggering portfolio scraping for {len(vcs_to_scrape)} VCs...")
                    scrape_response = requests.post(
                        f"{API_BASE}/portfolios/scrape",
                        json={"vc_ids": vcs_to_scrape},
                        timeout=300  # 5 minute timeout for comprehensive scraping
                    )
                    
                    if scrape_response.status_code == 200:
                        scrape_result = scrape_response.json()
                        results['yc_antler_scraping'] = scrape_result
                        print(f"   ✓ Scraping triggered: {scrape_result.get('message', 'Success')}")
                    else:
                        error_msg = f"Scraping failed: {scrape_response.status_code} - {scrape_response.text}"
                        print(f"   ✗ {error_msg}")
                        results['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"YC/Antler scraping error: {str(e)}"
            print(f"   ✗ {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 2: VC Auto-Discovery
        print("\n" + "="*80)
        print("[3/6] WORKFLOW 2: VC Auto-Discovery")
        print("="*80)
        print("   Triggering VC discovery from multiple sources...")
        print("   This will discover ALL active early-stage investors")
        
        try:
            discover_response = requests.post(
                f"{API_BASE}/portfolios/discover",
                timeout=600  # 10 minute timeout for discovery
            )
            
            if discover_response.status_code == 200:
                discover_result = discover_response.json()
                results['vc_discovery'] = discover_result
                print(f"   ✓ Discovered: {discover_result.get('discovered', 0)} VCs")
                print(f"   ✓ Added: {discover_result.get('added', 0)} new VCs")
            else:
                error_msg = f"Discovery failed: {discover_response.status_code} - {discover_response.text}"
                print(f"   ✗ {error_msg}")
                results['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"VC discovery error: {str(e)}"
            print(f"   ✗ {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 3: Scrape All VCs
        print("\n" + "="*80)
        print("[4/6] WORKFLOW 3: Scrape All VCs")
        print("="*80)
        print("   Triggering comprehensive scraping for ALL VCs...")
        
        try:
            # Get all VCs
            vcs_response = requests.get(f"{API_BASE}/investors", timeout=10)
            if vcs_response.status_code == 200:
                all_vcs = vcs_response.json()
                vc_ids = [vc['id'] for vc in all_vcs if vc.get('portfolio_url') or vc.get('url')]
                
                print(f"   Found {len(vc_ids)} VCs with portfolio URLs")
                
                if vc_ids:
                    # Scrape in batches to avoid timeout
                    batch_size = 5
                    total_scraped = 0
                    
                    for i in range(0, len(vc_ids), batch_size):
                        batch = vc_ids[i:i+batch_size]
                        print(f"   Scraping batch {i//batch_size + 1}/{(len(vc_ids)-1)//batch_size + 1} ({len(batch)} VCs)...")
                        
                        scrape_response = requests.post(
                            f"{API_BASE}/portfolios/scrape",
                            json={"vc_ids": batch},
                            timeout=600  # 10 minute timeout per batch
                        )
                        
                        if scrape_response.status_code == 200:
                            scrape_result = scrape_response.json()
                            batch_companies = scrape_result.get('companies_added', 0)
                            total_scraped += batch_companies
                            print(f"     ✓ Batch complete: {batch_companies} companies")
                        else:
                            print(f"     ✗ Batch failed: {scrape_response.status_code}")
                        
                        # Rate limiting between batches
                        if i + batch_size < len(vc_ids):
                            time.sleep(2)
                    
                    results['all_vcs_scraping'] = {
                        'vcs_scraped': len(vc_ids),
                        'total_companies': total_scraped
                    }
                    print(f"\n   ✓ Total: {total_scraped} companies from {len(vc_ids)} VCs")
                
        except Exception as e:
            error_msg = f"All VCs scraping error: {str(e)}"
            print(f"   ✗ {error_msg}")
            results['errors'].append(error_msg)
        
        # Workflow 4: Create Relationships
        print("\n" + "="*80)
        print("[5/6] WORKFLOW 4: Create Investor-Company Relationships")
        print("="*80)
        print("   Migrating source data to relationships...")
        
        try:
            migrate_response = requests.post(
                f"{API_BASE}/migrate/investor-relationships",
                timeout=60
            )
            
            if migrate_response.status_code == 200:
                migrate_result = migrate_response.json()
                results['relationships'] = migrate_result
                print(f"   ✓ Relationships created: {migrate_result.get('relationships_created', 0)}")
            else:
                error_msg = f"Migration failed: {migrate_response.status_code} - {migrate_response.text}"
                print(f"   ✗ {error_msg}")
                results['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"Relationship creation error: {str(e)}"
            print(f"   ✗ {error_msg}")
            results['errors'].append(error_msg)
        
        # Get final stats
        print("\n" + "="*80)
        print("[6/6] Getting final statistics...")
        print("="*80)
        
        try:
            stats_response = requests.get(f"{API_BASE}/stats", timeout=10)
            if stats_response.status_code == 200:
                results['final_stats'] = stats_response.json()
                
                initial_companies = results['initial_stats'].get('total_companies', 0)
                final_companies = results['final_stats'].get('total_companies', 0)
                initial_vcs = results['initial_stats'].get('total_vcs', 0)
                final_vcs = results['final_stats'].get('total_vcs', 0)
                
                print(f"\nCompanies:")
                print(f"  Initial: {initial_companies}")
                print(f"  Final: {final_companies}")
                print(f"  Added: {final_companies - initial_companies}")
                
                print(f"\nVCs:")
                print(f"  Initial: {initial_vcs}")
                print(f"  Final: {final_vcs}")
                print(f"  Added: {final_vcs - initial_vcs}")
                
                # Get relationship count
                relationships_response = requests.get(f"{API_BASE}/investors/relationships", timeout=10)
                if relationships_response.status_code == 200:
                    relationships = relationships_response.json()
                    print(f"\nRelationships: {len(relationships)}")
                    results['relationships']['total'] = len(relationships)
                
        except Exception as e:
            print(f"   Warning: Could not get final stats: {e}")
        
        print("\n" + "="*80)
        print("WORKFLOWS COMPLETE")
        print("="*80 + "\n")
        
        return results
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return results

if __name__ == "__main__":
    results = trigger_full_workflows()
    
    # Save results
    with open("workflow_results_api.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Results saved to workflow_results_api.json")

