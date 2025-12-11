"""
Simple YC batch scraper using direct HTTP requests
Extracts company names and domains from YC batch pages
"""
import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup
from typing import List, Dict

async def scrape_yc_batch_simple(batch: str) -> List[Dict]:
    """Scrape YC batch using simple HTTP request"""
    url = f"https://www.ycombinator.com/companies?batch={batch}"
    companies = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status == 200:
                    content = await response.text(encoding='utf-8', errors='ignore')
                    
                    # Try to find company data in JSON-LD or script tags
                    json_ld_match = re.search(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
                    if json_ld_match:
                        import json
                        try:
                            data = json.loads(json_ld_match.group(1))
                            if isinstance(data, dict) and 'itemListElement' in data:
                                for item in data['itemListElement']:
                                    if 'item' in item:
                                        name = item['item'].get('name', '')
                                        url_str = item['item'].get('url', '')
                                        if name:
                                            # Extract domain from URL
                                            domain_match = re.search(r'https?://([a-zA-Z0-9.-]+)', url_str)
                                            domain = domain_match.group(1) if domain_match else None
                                            if not domain:
                                                domain = name.lower().replace(' ', '').replace('-', '') + '.com'
                                            companies.append({
                                                'name': name,
                                                'domain': domain,
                                                'yc_batch': batch,
                                                'source': 'yc',
                                                'focus_areas': []
                                            })
                        except:
                            pass
                    
                    # Fallback: parse HTML
                    if not companies:
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Find all links to company pages
                        company_links = soup.find_all('a', href=re.compile(r'/companies/[^/]+'))
                        seen_names = set()
                        
                        for link in company_links:
                            company_name = link.get_text().strip()
                            href = link.get('href', '')
                            
                            if company_name and len(company_name) > 2 and company_name not in seen_names:
                                seen_names.add(company_name)
                                
                                # Try to extract domain from href
                                domain = None
                                if href:
                                    # YC URLs are like /companies/companyname
                                    company_slug = href.split('/')[-1]
                                    domain = company_slug + '.com'  # Fallback
                                
                                # Look for domain in nearby text
                                parent = link.parent
                                if parent:
                                    text = parent.get_text()
                                    domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})', text)
                                    if domain_match:
                                        domain = domain_match.group(1)
                                
                                if not domain:
                                    domain = company_name.lower().replace(' ', '').replace('-', '') + '.com'
                                
                                companies.append({
                                    'name': company_name,
                                    'domain': domain,
                                    'yc_batch': batch,
                                    'source': 'yc',
                                    'focus_areas': []
                                })
                    
        except Exception as e:
            print(f"Error scraping YC batch {batch}: {e}")
    
    return companies

async def scrape_all_yc_batches() -> List[Dict]:
    """Scrape all recent YC batches"""
    batches = ['W22', 'S22', 'W23', 'S23']
    all_companies = []
    
    for batch in batches:
        print(f"Scraping YC batch {batch}...")
        companies = await scrape_yc_batch_simple(batch)
        print(f"  Found {len(companies)} companies")
        all_companies.extend(companies)
        await asyncio.sleep(1)  # Rate limiting
    
    # Deduplicate by name
    seen = set()
    unique = []
    for company in all_companies:
        name_lower = company['name'].lower()
        if name_lower not in seen:
            seen.add(name_lower)
            unique.append(company)
    
    return unique

if __name__ == "__main__":
    companies = asyncio.run(scrape_all_yc_batches())
    print(f"\nTotal unique companies: {len(companies)}")
    for company in companies[:10]:
        print(f"  - {company['name']} ({company['domain']})")


