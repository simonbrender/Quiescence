"""Test script for portfolio scraper"""
import sys
import asyncio
from portfolio_scraper_enhanced import EnhancedPortfolioScraper

async def test_yc_scraper():
    """Test YC scraper with small limit"""
    print("=" * 60)
    print("Testing YC Portfolio Scraper (limit: 50 companies)")
    print("=" * 60)
    
    scraper = EnhancedPortfolioScraper()
    try:
        companies = await scraper.scrape_yc_portfolio(max_companies=50)
        print(f"\n[SUCCESS] YC Scraper: Found {len(companies)} companies")
        
        if companies:
            print("\nSample companies:")
            for i, company in enumerate(companies[:10], 1):
                print(f"  {i}. {company.get('name', 'N/A')} ({company.get('domain', 'N/A')})")
                print(f"     Source: {company.get('source')}, Batch: {company.get('yc_batch', 'N/A')}")
            
            # Data quality checks
            print("\n[QUALITY] Data Quality Analysis:")
            with_domains = sum(1 for c in companies if c.get('domain'))
            with_names = sum(1 for c in companies if c.get('name'))
            print(f"  Companies with domains: {with_domains}/{len(companies)} ({with_domains/len(companies)*100:.1f}%)")
            print(f"  Companies with names: {with_names}/{len(companies)} ({with_names/len(companies)*100:.1f}%)")
            
            # Check for duplicates
            domains = [c.get('domain') for c in companies if c.get('domain')]
            names = [c.get('name', '').lower() for c in companies if c.get('name')]
            unique_domains = len(set(domains))
            unique_names = len(set(names))
            print(f"  Unique domains: {unique_domains}/{len(domains)}")
            print(f"  Unique names: {unique_names}/{len(names)}")
            
            # Validate domain format
            valid_domains = []
            for domain in domains:
                if domain and '.' in domain and len(domain.split('.')) >= 2:
                    if len(domain) >= 4 and len(domain) <= 255:
                        valid_domains.append(domain)
            print(f"  Valid domain format: {len(valid_domains)}/{len(domains)}")
            
        return companies
    except Exception as e:
        print(f"\n[ERROR] YC Scraper Error: {e}")
        import traceback
        traceback.print_exc()
        return []

async def test_antler_scraper():
    """Test Antler scraper with small limit"""
    print("\n" + "=" * 60)
    print("Testing Antler Portfolio Scraper (limit: 50 companies)")
    print("=" * 60)
    
    scraper = EnhancedPortfolioScraper()
    try:
        companies = await scraper.scrape_antler_portfolio(max_companies=50)
        print(f"\n[SUCCESS] Antler Scraper: Found {len(companies)} companies")
        
        if companies:
            print("\nSample companies:")
            for i, company in enumerate(companies[:10], 1):
                print(f"  {i}. {company.get('name', 'N/A')} ({company.get('domain', 'N/A')})")
                print(f"     Source: {company.get('source')}, Year: {company.get('year', 'N/A')}")
            
            # Data quality checks
            print("\n[QUALITY] Data Quality Analysis:")
            with_domains = sum(1 for c in companies if c.get('domain'))
            with_names = sum(1 for c in companies if c.get('name'))
            print(f"  Companies with domains: {with_domains}/{len(companies)} ({with_domains/len(companies)*100:.1f}%)")
            print(f"  Companies with names: {with_names}/{len(companies)} ({with_names/len(companies)*100:.1f}%)")
            
            # Check for duplicates
            domains = [c.get('domain') for c in companies if c.get('domain')]
            names = [c.get('name', '').lower() for c in companies if c.get('name')]
            unique_domains = len(set(domains))
            unique_names = len(set(names))
            print(f"  Unique domains: {unique_domains}/{len(domains)}")
            print(f"  Unique names: {unique_names}/{len(names)}")
            
        return companies
    except Exception as e:
        print(f"\n[ERROR] Antler Scraper Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("Starting portfolio scraper tests...")
    print("This will test both YC and Antler scrapers with small limits\n")
    
    yc_companies = asyncio.run(test_yc_scraper())
    antler_companies = asyncio.run(test_antler_scraper())
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"YC: {len(yc_companies)} companies")
    print(f"Antler: {len(antler_companies)} companies")
    print(f"Total: {len(yc_companies) + len(antler_companies)} companies")
    
    if len(yc_companies) > 0 and len(antler_companies) > 0:
        print("\n[SUCCESS] Both scrapers working!")
    elif len(yc_companies) > 0 or len(antler_companies) > 0:
        print("\n[WARNING] One scraper working, one may need fixes")
    else:
        print("\n[ERROR] Scrapers need debugging")

