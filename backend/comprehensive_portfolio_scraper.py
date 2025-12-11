"""
Comprehensive Portfolio Scraper
Ensures we get ALL companies from YC and Antler portfolios
"""
import asyncio
import sys
import duckdb
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent))

from portfolio_scraper_observable import ObservablePortfolioScraper


async def scrape_all_portfolios():
    """Scrape all portfolios comprehensively"""
    print("=" * 80)
    print("COMPREHENSIVE PORTFOLIO SCRAPING")
    print("=" * 80)
    
    scraper = ObservablePortfolioScraper()
    
    # Scrape YC portfolio (target: 1,000-5,000 companies)
    print("\n[STEP 1] Scraping YC Portfolio...")
    print("Target: 1,000-5,000 companies")
    yc_companies = await scraper.scrape_yc_portfolio_observable(max_companies=5000)
    print(f"✅ YC: Found {len(yc_companies)} companies")
    
    # Scrape Antler portfolio (target: 1,267 companies)
    print("\n[STEP 2] Scraping Antler Portfolio...")
    print("Target: 1,267 companies")
    antler_companies = await scraper.scrape_antler_portfolio_observable(max_companies=2000)
    print(f"✅ Antler: Found {len(antler_companies)} companies")
    
    # Store in database
    print("\n[STEP 3] Storing companies in database...")
    db_path = Path(__file__).parent / "celerio_scout.db"
    conn = duckdb.connect(str(db_path))
    
    stored_count = 0
    for company in yc_companies + antler_companies:
        try:
            domain = company.get('domain', '').strip()
            if not domain:
                continue
            
            # Check if exists
            existing = conn.execute(
                "SELECT id FROM companies WHERE domain = ?",
                (domain,)
            ).fetchone()
            
            if not existing:
                company_id = abs(hash(domain)) % 1000000
                conn.execute("""
                    INSERT INTO companies 
                    (id, name, domain, source, yc_batch, focus_areas, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company_id,
                    company.get('name', ''),
                    domain,
                    company.get('source', 'portfolio'),
                    company.get('yc_batch', ''),
                    json.dumps(company.get('focus_areas', [])),
                    datetime.now(),
                    datetime.now()
                ))
                stored_count += 1
        except Exception as e:
            print(f"Error storing {company.get('name')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ Stored {stored_count} new companies")
    print(f"\nTotal companies scraped:")
    print(f"  YC: {len(yc_companies)}")
    print(f"  Antler: {len(antler_companies)}")
    print(f"  New companies stored: {stored_count}")
    
    return {
        'yc': len(yc_companies),
        'antler': len(antler_companies),
        'stored': stored_count
    }


if __name__ == "__main__":
    results = asyncio.run(scrape_all_portfolios())
    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE!")
    print("=" * 80)

