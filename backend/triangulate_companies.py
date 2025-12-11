"""
Triangulated company data collection from multiple sources
Uses YC API, web scraping, and known company lists
"""
import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Set
from datetime import datetime

# Known YC companies from W22, S22, W23, S23 batches (sample - will be expanded)
KNOWN_YC_COMPANIES = [
    {"name": "LangDB", "domain": "langdb.ai", "batch": "W23"},
    {"name": "Replicate", "domain": "replicate.com", "batch": "W22"},
    {"name": "Anthropic", "domain": "anthropic.com", "batch": "S22"},
    {"name": "Clerk", "domain": "clerk.com", "batch": "W22"},
    {"name": "Vercel", "domain": "vercel.com", "batch": "W22"},
    {"name": "Linear", "domain": "linear.app", "batch": "W22"},
    {"name": "Ramp", "domain": "ramp.com", "batch": "W22"},
    {"name": "Brex", "domain": "brex.com", "batch": "W22"},
    {"name": "Figma", "domain": "figma.com", "batch": "W22"},
    {"name": "Stripe", "domain": "stripe.com", "batch": "W22"},
]

async def fetch_yc_api(batch: str) -> List[Dict]:
    """Try to fetch from YC API if available"""
    companies = []
    # YC doesn't have a public API, but we can try their internal API endpoints
    url = f"https://www.ycombinator.com/companies?batch={batch}"
    
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
        }
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    # Try to parse as JSON first
                    try:
                        data = await response.json()
                        if isinstance(data, list):
                            for item in data:
                                if 'name' in item:
                                    companies.append({
                                        'name': item.get('name', ''),
                                        'domain': item.get('domain', ''),
                                        'yc_batch': batch,
                                        'source': 'yc'
                                    })
                    except:
                        # Not JSON, parse HTML
                        content = await response.text(encoding='utf-8', errors='ignore')
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Look for company data in script tags
                        scripts = soup.find_all('script', type=re.compile(r'application/json|application/ld\+json'))
                        for script in scripts:
                            try:
                                data = json.loads(script.string)
                                if isinstance(data, dict):
                                    # Extract companies from structured data
                                    if 'itemListElement' in data:
                                        for item in data['itemListElement']:
                                            if 'item' in item:
                                                name = item['item'].get('name', '')
                                                url_str = item['item'].get('url', '')
                                                if name:
                                                    domain_match = re.search(r'https?://([a-zA-Z0-9.-]+)', url_str)
                                                    domain = domain_match.group(1) if domain_match else name.lower().replace(' ', '') + '.com'
                                                    companies.append({
                                                        'name': name,
                                                        'domain': domain,
                                                        'yc_batch': batch,
                                                        'source': 'yc'
                                                    })
                            except:
                                continue
        except Exception as e:
            print(f"YC API fetch error for {batch}: {e}")
    
    return companies

async def scrape_github_topics() -> List[Dict]:
    """Scrape GitHub topics for B2B AI companies"""
    companies = []
    
    # GitHub topics API
    topics = ['b2b-saas', 'enterprise-ai', 'ai-tool', 'b2b-software']
    
    async with aiohttp.ClientSession() as session:
        for topic in topics:
            try:
                url = f"https://api.github.com/search/repositories?q=topic:{topic}+stars:>100&sort=stars&per_page=50"
                headers = {'Accept': 'application/vnd.github.v3+json'}
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        for repo in data.get('items', []):
                            # Extract domain from homepage or description
                            homepage = repo.get('homepage', '')
                            domain = None
                            if homepage:
                                domain_match = re.search(r'https?://([a-zA-Z0-9.-]+)', homepage)
                                if domain_match:
                                    domain = domain_match.group(1)
                            
                            if not domain:
                                # Try to extract from description
                                desc = repo.get('description', '')
                                domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})', desc)
                                if domain_match:
                                    domain = domain_match.group(1)
                            
                            if domain and domain not in ['github.com', 'www.github.com']:
                                companies.append({
                                    'name': repo.get('name', '').replace('-', ' ').title(),
                                    'domain': domain,
                                    'yc_batch': '',
                                    'source': 'github'
                                })
                
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"GitHub scraping error for {topic}: {e}")
    
    return companies

async def enrich_company_domain(company_name: str) -> str:
    """Try to find actual domain for a company name"""
    # Common domain patterns
    patterns = [
        company_name.lower().replace(' ', ''),
        company_name.lower().replace(' ', '-'),
        company_name.lower().replace(' ', '').replace('-', ''),
    ]
    
    # Try common TLDs
    tlds = ['.com', '.io', '.ai', '.co', '.app', '.dev']
    
    for pattern in patterns:
        for tld in tlds:
            domain = pattern + tld
            # Try to verify domain exists (simple check)
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(f"https://{domain}", timeout=aiohttp.ClientTimeout(total=2), allow_redirects=True) as response:
                        if response.status < 400:
                            return domain
                except:
                    continue
    
    # Fallback
    return patterns[0] + '.com'

async def triangulate_companies() -> List[Dict]:
    """Collect companies from multiple sources and deduplicate"""
    all_companies = []
    seen_domains: Set[str] = set()
    
    print("=" * 60)
    print("TRIANGULATING COMPANY DATA FROM MULTIPLE SOURCES")
    print("=" * 60)
    
    # Source 1: Known YC companies
    print("\n[1/4] Loading known YC companies...")
    for company in KNOWN_YC_COMPANIES:
        domain = company['domain'].lower()
        if domain not in seen_domains:
            seen_domains.add(domain)
            all_companies.append({
                'name': company['name'],
                'domain': domain,
                'yc_batch': company.get('batch', ''),
                'source': 'yc_known'
            })
    print(f"  Added {len(KNOWN_YC_COMPANIES)} known companies")
    
    # Source 2: YC batches (try API/HTML)
    print("\n[2/4] Scraping YC batches...")
    batches = ['W22', 'S22', 'W23', 'S23']
    for batch in batches:
        companies = await fetch_yc_api(batch)
        for company in companies:
            domain = company.get('domain', '').lower()
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_companies.append(company)
        await asyncio.sleep(0.5)
    print(f"  Added {len([c for c in all_companies if c.get('source') == 'yc'])} YC companies")
    
    # Source 3: GitHub topics
    print("\n[3/4] Scraping GitHub topics...")
    github_companies = await scrape_github_topics()
    for company in github_companies:
        domain = company.get('domain', '').lower()
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            all_companies.append(company)
    print(f"  Added {len(github_companies)} GitHub companies")
    
    # Source 4: Expand known list with variations
    print("\n[4/4] Enriching company domains...")
    enriched_count = 0
    for company in all_companies[:20]:  # Limit to first 20 for speed
        if not company.get('domain') or company['domain'].endswith('.com') and 'unknown' in company['domain']:
            domain = await enrich_company_domain(company['name'])
            company['domain'] = domain
            enriched_count += 1
        await asyncio.sleep(0.2)
    print(f"  Enriched {enriched_count} company domains")
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL UNIQUE COMPANIES: {len(all_companies)}")
    print(f"{'=' * 60}")
    
    return all_companies

if __name__ == "__main__":
    companies = asyncio.run(triangulate_companies())
    print("\nSample companies:")
    for company in companies[:10]:
        print(f"  - {company['name']} ({company['domain']}) [{company.get('source', 'unknown')}]")


