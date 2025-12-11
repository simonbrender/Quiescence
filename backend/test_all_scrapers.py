"""Test all scrapers"""
import asyncio
import sys
sys.path.insert(0, '.')

from portfolio_scraper import PortfolioScraper

async def test_all():
    scraper = PortfolioScraper()
    
    # Test YC
    print('\n=== Testing Y Combinator ===')
    yc_result = await scraper.scrape_portfolio('Y Combinator', 'https://www.ycombinator.com/companies', 'Accelerator')
    print(f'Found {len(yc_result)} companies')
    print('First 15 companies:')
    for i, c in enumerate(yc_result[:15], 1):
        print(f'{i}. {c["name"]}')
    
    # Test Antler
    print('\n=== Testing Antler ===')
    antler_result = await scraper.scrape_portfolio('Antler', 'https://www.antler.co/portfolio', 'Accelerator')
    print(f'Found {len(antler_result)} companies')
    print('First 10 companies:')
    for i, c in enumerate(antler_result[:10], 1):
        print(f'{i}. {c["name"]}')
    
    # Test NFX
    print('\n=== Testing NFX ===')
    nfx_result = await scraper.scrape_portfolio('NFX', 'https://www.nfx.com', 'VC')
    print(f'Found {len(nfx_result)} companies')
    print('First 10 companies:')
    for i, c in enumerate(nfx_result[:10], 1):
        print(f'{i}. {c["name"]} - {c.get("domain", "(no domain)")}')
    
    await scraper.close()
    
    print('\n=== Summary ===')
    print(f'YC: {len(yc_result)} companies')
    print(f'Antler: {len(antler_result)} companies')
    print(f'NFX: {len(nfx_result)} companies')
    print(f'Total: {len(yc_result) + len(antler_result) + len(nfx_result)} companies')

if __name__ == '__main__':
    asyncio.run(test_all())


