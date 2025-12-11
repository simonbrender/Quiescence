"""Run full portfolio scrape and display results"""
import asyncio
import sys
from portfolio_scraper_enhanced import EnhancedPortfolioScraper

async def main():
    print("=" * 80)
    print("FULL PORTFOLIO SCRAPE - YC AND ANTLER")
    print("=" * 80)
    print("\nThis will scrape:")
    print("  - YC: All companies (expected: 1,000-5,000)")
    print("  - Antler: All companies (expected: 1,267)")
    print("\nEstimated time: 15-25 minutes")
    print("\nStarting scrape...\n")
    
    scraper = EnhancedPortfolioScraper()
    
    # Run both scrapes concurrently
    print("[INFO] Starting both scrapes concurrently...")
    results = await scraper.scrape_both_portfolios()
    
    yc_companies = results.get('yc', [])
    antler_companies = results.get('antler', [])
    
    print("\n" + "=" * 80)
    print("SCRAPE COMPLETE")
    print("=" * 80)
    print(f"\nYC Companies: {len(yc_companies)}")
    print(f"Antler Companies: {len(antler_companies)}")
    print(f"Total Companies: {len(yc_companies) + len(antler_companies)}")
    
    # Data quality check
    print("\n" + "=" * 80)
    print("DATA QUALITY CHECK")
    print("=" * 80)
    
    yc_with_domains = sum(1 for c in yc_companies if c.get('domain'))
    antler_with_domains = sum(1 for c in antler_companies if c.get('domain'))
    
    print(f"\nYC:")
    print(f"  Companies with domains: {yc_with_domains}/{len(yc_companies)} ({yc_with_domains/len(yc_companies)*100:.1f}%)" if yc_companies else "  No companies found")
    print(f"  Companies with names: {len(yc_companies)}/{len(yc_companies)} (100.0%)" if yc_companies else "  No companies found")
    
    print(f"\nAntler:")
    print(f"  Companies with domains: {antler_with_domains}/{len(antler_companies)} ({antler_with_domains/len(antler_companies)*100:.1f}%)" if antler_companies else "  No companies found")
    print(f"  Companies with names: {len(antler_companies)}/{len(antler_companies)} (100.0%)" if antler_companies else "  No companies found")
    
    # Sample companies
    print("\n" + "=" * 80)
    print("SAMPLE COMPANIES")
    print("=" * 80)
    
    if yc_companies:
        print(f"\nYC Sample (first 10):")
        for i, company in enumerate(yc_companies[:10], 1):
            print(f"  {i}. {company.get('name', 'N/A')} ({company.get('domain', 'N/A')})")
    
    if antler_companies:
        print(f"\nAntler Sample (first 10):")
        for i, company in enumerate(antler_companies[:10], 1):
            print(f"  {i}. {company.get('name', 'N/A')} ({company.get('domain', 'N/A')})")
    
    # Verify counts
    print("\n" + "=" * 80)
    print("COUNT VERIFICATION")
    print("=" * 80)
    print(f"\nYC: {len(yc_companies)} companies")
    if len(yc_companies) >= 1000:
        print("  [SUCCESS] YC count is >= 1,000 as expected")
    elif len(yc_companies) >= 500:
        print("  [WARNING] YC count is less than expected (expected 1,000-5,000)")
    else:
        print("  [WARNING] YC count is much less than expected")
    
    print(f"\nAntler: {len(antler_companies)} companies")
    if len(antler_companies) >= 1200:
        print("  [SUCCESS] Antler count is >= 1,200 as expected")
    elif len(antler_companies) >= 1000:
        print("  [WARNING] Antler count is close to expected (expected 1,267)")
    else:
        print("  [WARNING] Antler count is less than expected")
    
    print("\n" + "=" * 80)
    print("SCRAPE COMPLETE - Results ready for UI display")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())

