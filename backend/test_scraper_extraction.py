"""Test what the portfolio scraper actually extracts"""
import asyncio
from portfolio_scraper_observable import ObservablePortfolioScraper

async def test_scraper():
    """Test scraper extraction"""
    scraper = ObservablePortfolioScraper()
    
    # Track what companies are found
    found_companies = []
    
    def progress_callback(event):
        if event.get('type') == 'progress' and 'companies_batch' in event:
            batch = event.get('companies_batch', [])
            if batch:
                found_companies.extend(batch)
                print(f"[PROGRESS] Found {len(batch)} companies in batch")
                for c in batch[:5]:  # Show first 5
                    print(f"  - {c.get('name')} ({c.get('domain')})")
        elif event.get('type') == 'complete':
            print(f"[COMPLETE] Total companies found: {event.get('companies_found', 0)}")
        elif event.get('type') == 'error':
            print(f"[ERROR] {event.get('error', 'Unknown error')}")
    
    scraper.progress_callback = progress_callback
    
    print("Testing YC portfolio scraper...")
    yc_companies = await scraper.scrape_yc_portfolio_observable(max_companies=50)
    
    print(f"\n=== RESULTS ===")
    print(f"Total YC companies extracted: {len(yc_companies)}")
    print(f"\nFirst 10 companies:")
    for i, c in enumerate(yc_companies[:10], 1):
        print(f"{i}. {c.get('name')} - {c.get('domain')}")
    
    # Check against known mock companies
    mock_names = {'stagnantai', 'rocketship', 'healthyscale', 'techjargon', 'silentgrowth'}
    real_companies = [c for c in yc_companies if c.get('name', '').lower() not in mock_names]
    
    print(f"\nReal companies (not mock): {len(real_companies)}")
    for c in real_companies[:10]:
        print(f"  - {c.get('name')} ({c.get('domain')})")

if __name__ == "__main__":
    asyncio.run(test_scraper())

