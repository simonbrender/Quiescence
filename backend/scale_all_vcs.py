"""
Scale All VCs - Comprehensive Portfolio Scraping System
Scrapes ALL VCs in database, removes limits, processes in parallel
"""
import asyncio
import duckdb
import json
from datetime import datetime
from typing import List, Dict
try:
    from comprehensive_portfolio_scraper_v2 import ComprehensivePortfolioScraper
except ImportError:
    # Fallback if module not found
    ComprehensivePortfolioScraper = None

try:
    from portfolio_scraper_enhanced import EnhancedPortfolioScraper, PortfolioConfig
except ImportError:
    EnhancedPortfolioScraper = None
    PortfolioConfig = None


async def scrape_all_vcs_comprehensive(db_conn) -> Dict[str, Dict]:
    """
    Scrape ALL VCs comprehensively
    Returns dict with stats and companies per VC
    """
    results = {
        'total_vcs': 0,
        'successful_scrapes': 0,
        'failed_scrapes': 0,
        'total_companies': 0,
        'vc_results': {}
    }
    
    # Get all VCs
    vc_results = db_conn.execute("""
        SELECT firm_name, portfolio_url, url, type, domain
        FROM vcs 
        WHERE (portfolio_url IS NOT NULL AND portfolio_url != '') 
           OR (url IS NOT NULL AND url != '')
        ORDER BY firm_name
    """).fetchall()
    
    results['total_vcs'] = len(vc_results)
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE VC SCRAPING - {len(vc_results)} VCs")
    print(f"{'='*80}\n")
    
    # Process in batches to avoid overwhelming
    batch_size = 5
    for batch_start in range(0, len(vc_results), batch_size):
        batch = vc_results[batch_start:batch_start + batch_size]
        
        tasks = []
        for row in batch:
            firm_name = row[0]
            portfolio_url = row[1] or row[2]
            vc_type = row[3] or 'VC'
            
            task = scrape_single_vc(firm_name, portfolio_url, vc_type)
            tasks.append((firm_name, task))
        
        # Execute batch in parallel
        for firm_name, task in tasks:
            try:
                companies = await task
                results['vc_results'][firm_name] = {
                    'companies': companies,
                    'count': len(companies),
                    'status': 'success'
                }
                results['successful_scrapes'] += 1
                results['total_companies'] += len(companies)
                print(f"✓ {firm_name}: {len(companies)} companies")
            except Exception as e:
                results['vc_results'][firm_name] = {
                    'companies': [],
                    'count': 0,
                    'status': 'failed',
                    'error': str(e)
                }
                results['failed_scrapes'] += 1
                print(f"✗ {firm_name}: Failed - {e}")
        
        # Rate limiting between batches
        if batch_start + batch_size < len(vc_results):
            await asyncio.sleep(2)
    
    return results


async def scrape_single_vc(firm_name: str, portfolio_url: str, vc_type: str) -> List[Dict]:
    """Scrape a single VC portfolio"""
    
    # Special handling for known VCs
    if firm_name == "Y Combinator":
        scraper = ComprehensivePortfolioScraper()
        companies = await scraper.scrape_yc_comprehensive()
        await scraper.close_session()
        return companies
    
    elif firm_name == "Antler":
        scraper = ComprehensivePortfolioScraper()
        companies = await scraper.scrape_antler_comprehensive()
        await scraper.close_session()
        return companies
    
    else:
        # Use enhanced scraper for generic portfolios
        scraper = EnhancedPortfolioScraper()
        
        config = PortfolioConfig(
            name=firm_name,
            url=portfolio_url,
            scroll_type="infinite",  # Most use infinite scroll
            max_companies=10000,  # NO LIMIT
            max_scroll_attempts=1000,  # Increased for comprehensive scraping
            scroll_wait_time=2.0,
            max_no_change_count=10  # More patience
        )
        
        companies = await scraper.scrape_portfolio(config)
        return companies


async def main():
    """Main execution"""
    # Connect to database
    conn = duckdb.connect("celerio_scout.db")
    
    print("\n" + "="*80)
    print("SCALING TEST - COMPREHENSIVE VC PORTFOLIO SCRAPING")
    print("="*80)
    
    # Step 1: YC Comprehensive
    print("\n[STEP 1] YC Comprehensive Scraping...")
    yc_scraper = ComprehensivePortfolioScraper()
    yc_companies = await yc_scraper.scrape_yc_comprehensive()
    await yc_scraper.close_session()
    print(f"YC Result: {len(yc_companies)} companies")
    
    # Step 2: Antler Comprehensive
    print("\n[STEP 2] Antler Comprehensive Scraping...")
    antler_scraper = ComprehensivePortfolioScraper()
    antler_companies = await antler_scraper.scrape_antler_comprehensive()
    await antler_scraper.close_session()
    print(f"Antler Result: {len(antler_companies)} companies")
    
    # Step 3: All Other VCs
    print("\n[STEP 3] Scraping ALL Other VCs...")
    all_vc_results = await scrape_all_vcs_comprehensive(conn)
    
    print("\n" + "="*80)
    print("SCALING RESULTS")
    print("="*80)
    print(f"YC Companies: {len(yc_companies)}")
    print(f"Antler Companies: {len(antler_companies)}")
    print(f"Other VCs Scraped: {all_vc_results['successful_scrapes']}/{all_vc_results['total_vcs']}")
    print(f"Other VC Companies: {all_vc_results['total_companies']}")
    print(f"\nTOTAL COMPANIES: {len(yc_companies) + len(antler_companies) + all_vc_results['total_companies']}")
    print("="*80)
    
    conn.close()


if __name__ == "__main__":
    asyncio.run(main())

