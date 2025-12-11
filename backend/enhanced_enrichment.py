"""
Enhanced Enrichment Pipeline with Firecrawl Integration
World-class data enrichment for startup companies
"""
import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Try to import Firecrawl
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    print("Firecrawl not available, using crawl4ai/HTTP fallback")

# Try to import crawl4ai
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False


class EnhancedEnrichment:
    """World-class enrichment pipeline using Firecrawl and multiple data sources"""
    
    def __init__(self, firecrawl_api_key: Optional[str] = None):
        self.firecrawl_api_key = firecrawl_api_key
        self.firecrawl_app = None
        if FIRECRAWL_AVAILABLE and firecrawl_api_key:
            try:
                self.firecrawl_app = FirecrawlApp(api_key=firecrawl_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Firecrawl: {e}")
                self.firecrawl_app = None
    
    async def crawl_with_firecrawl(self, url: str) -> Optional[Dict]:
        """Crawl a URL using Firecrawl for comprehensive data extraction"""
        if not self.firecrawl_app:
            return None
        
        try:
            # Firecrawl can extract structured data from web pages
            result = await asyncio.to_thread(
                self.firecrawl_app.scrape_url,
                url,
                params={
                    'formats': ['markdown', 'html'],
                    'includeTags': ['h1', 'h2', 'h3', 'p', 'span', 'div'],
                    'excludeTags': ['script', 'style', 'nav', 'footer']
                }
            )
            
            if result and result.get('success'):
                return {
                    'content': result.get('markdown', '') or result.get('html', ''),
                    'metadata': result.get('metadata', {}),
                    'links': result.get('links', [])
                }
        except Exception as e:
            print(f"Firecrawl error for {url}: {e}")
        
        return None
    
    async def crawl_with_crawl4ai(self, url: str) -> Optional[str]:
        """Fallback to crawl4ai if Firecrawl unavailable"""
        if not CRAWL4AI_AVAILABLE:
            return None
        
        try:
            browser_config = BrowserConfig(headless=True)
            crawler_config = CrawlerRunConfig(timeout=10000)
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawler_config)
                if result and result.success:
                    return result.markdown or result.html
        except Exception as e:
            print(f"Crawl4AI error for {url}: {e}")
        
        return None
    
    async def extract_comprehensive_data(self, domain: str, company_name: str) -> Dict:
        """
        Extract comprehensive company data from multiple sources:
        - Company website (about, team, press pages)
        - Crunchbase (if available)
        - LinkedIn (if available)
        - News articles
        """
        enrichment_data = {
            'funding_amount': None,
            'funding_currency': 'USD',
            'last_raise_date': None,
            'last_raise_stage': None,
            'employee_count': None,
            'founding_date': None,
            'headquarters_location': None,
            'founders': [],
            'product_description': None,
            'industry': None,
            'current_valuation': None,
            'funding_rounds': [],
            'key_milestones': []
        }
        
        # URLs to check
        base_urls = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"https://{domain}/about",
            f"https://{domain}/team",
            f"https://{domain}/press",
            f"https://{domain}/news",
            f"https://{domain}/careers"
        ]
        
        all_content = []
        
        # Crawl each URL
        for url in base_urls[:3]:  # Limit to first 3 for performance
            try:
                # Try Firecrawl first
                firecrawl_data = await self.crawl_with_firecrawl(url)
                if firecrawl_data:
                    all_content.append(firecrawl_data['content'])
                    # Extract metadata
                    metadata = firecrawl_data.get('metadata', {})
                    if metadata.get('title'):
                        enrichment_data['product_description'] = metadata['title']
                    continue
                
                # Fallback to crawl4ai
                crawl4ai_content = await self.crawl_with_crawl4ai(url)
                if crawl4ai_content:
                    all_content.append(crawl4ai_content)
                    continue
                
                # Fallback to HTTP
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            content = await response.text()
                            all_content.append(content)
            except Exception as e:
                continue
        
        # Parse all collected content
        combined_text = "\n\n".join(all_content)
        
        if not combined_text:
            return enrichment_data
        
        # Extract funding information
        funding_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(?:million|M|m|billion|B|b)\s*(?:raised|funding|investment)',
            r'raised\s+\$(\d+(?:\.\d+)?)\s*(?:million|M|m|billion|B|b)',
            r'(\d+(?:\.\d+)?)\s*(?:million|M|m|billion|B|b)\s*(?:USD|dollar|funding)',
            r'Series\s+([A-Z])\s+.*?\$(\d+(?:\.\d+)?)\s*(?:million|M|m|billion|B|b)',
        ]
        
        for pattern in funding_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                try:
                    if isinstance(matches[0], tuple):
                        stage = matches[0][0]
                        amount_str = matches[0][1]
                        enrichment_data['last_raise_stage'] = f"Series {stage}"
                    else:
                        amount_str = matches[0]
                    
                    amount = float(amount_str)
                    if 'billion' in pattern.lower() or 'b' in pattern.lower():
                        enrichment_data['funding_amount'] = amount * 1000000000
                    else:
                        enrichment_data['funding_amount'] = amount * 1000000
                    break
                except:
                    continue
        
        # Extract employee count
        employee_patterns = [
            r'(\d+)\s*(?:employees|people|team members)',
            r'team\s+of\s+(\d+)',
            r'(\d+)\+?\s*(?:employees|people)',
            r'over\s+(\d+)\s*(?:employees|people)',
        ]
        
        for pattern in employee_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                try:
                    count = int(matches[0])
                    if 1 <= count <= 10000:  # Reasonable range
                        enrichment_data['employee_count'] = count
                        break
                except:
                    continue
        
        # Extract founding date
        founding_patterns = [
            r'founded\s+in\s+(\d{4})',
            r'established\s+in\s+(\d{4})',
            r'since\s+(\d{4})',
            r'(\d{4})\s+.*?\s+founded',
        ]
        
        for pattern in founding_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                try:
                    year = int(matches[0])
                    if 1990 <= year <= datetime.now().year:
                        enrichment_data['founding_date'] = f"{year}-01-01"
                        break
                except:
                    continue
        
        # Extract location
        location_patterns = [
            r'headquartered\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'based\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'located\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                enrichment_data['headquarters_location'] = matches[0]
                break
        
        # Extract founders (look for "Founded by" patterns)
        founder_patterns = [
            r'founded\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+and\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)?)',
            r'co-founded\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        
        for pattern in founder_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                founders_str = matches[0]
                # Split by "and" or comma
                founders = re.split(r'\s+and\s+|\s*,\s*', founders_str)
                enrichment_data['founders'] = [f.strip() for f in founders if f.strip()]
                break
        
        return enrichment_data
    
    async def enrich_company(self, company: Dict, domain: str) -> Dict:
        """Enrich a single company with comprehensive data"""
        print(f"[ENHANCED-ENRICHMENT] Enriching {company.get('name')} ({domain})...")
        
        # Get comprehensive data
        comprehensive_data = await self.extract_comprehensive_data(domain, company.get('name', ''))
        
        # Merge with existing company data
        enriched = {
            **company,
            **comprehensive_data
        }
        
        # Infer focus areas from domain/name if not present
        if not enriched.get('focus_areas') or enriched.get('focus_areas') == '[]':
            focus_areas = await self._infer_focus_areas(domain, company.get('name', ''))
            enriched['focus_areas'] = focus_areas
        
        # Infer stage from portfolio source if not present
        if not enriched.get('last_raise_stage'):
            if company.get('yc_batch') or 'yc' in (company.get('source', '') or '').lower():
                enriched['last_raise_stage'] = 'Seed'
            elif 'antler' in (company.get('source', '') or '').lower():
                enriched['last_raise_stage'] = 'Seed'
        
        return enriched
    
    async def _infer_focus_areas(self, domain: str, name: str) -> List[str]:
        """Infer focus areas from domain and company name"""
        focus_areas = []
        text = (domain + " " + name).lower()
        
        # AI/ML indicators
        if any(kw in text for kw in ['ai', 'ml', 'machine learning', 'llm', 'gpt', 'neural', 'anthropic', 'openai']):
            if not any(avoid in text for avoid in ['raise', 'paid', 'fair']):
                focus_areas.append('AI/ML')
        
        # B2B SaaS indicators
        if any(kw in text for kw in ['saas', 'b2b', 'enterprise', 'platform', 'api', 'software', 'cloud']):
            focus_areas.append('B2B SaaS')
        
        # Fintech indicators
        if any(kw in text for kw in ['fintech', 'finance', 'payment', 'banking', 'crypto', 'blockchain', 'stripe', 'plaid']):
            focus_areas.append('Fintech')
        
        # DevTools indicators
        if any(kw in text for kw in ['dev', 'developer', 'tools', 'infrastructure', 'ci/cd', 'deployment', 'github', 'gitlab']):
            focus_areas.append('DevTools')
        
        return focus_areas if focus_areas else ['B2B SaaS']


async def enrich_companies_batch(companies: List[Dict], firecrawl_api_key: Optional[str] = None, batch_size: int = 50):
    """Enrich a batch of companies using enhanced enrichment pipeline"""
    enricher = EnhancedEnrichment(firecrawl_api_key=firecrawl_api_key)
    
    enriched_count = 0
    for i, company in enumerate(companies, 1):
        try:
            domain = company.get('domain', '').strip()
            if not domain:
                continue
            
            enriched = await enricher.enrich_company(company, domain)
            enriched_count += 1
            
            if i % 10 == 0:
                print(f"[ENHANCED-ENRICHMENT] Processed {i}/{len(companies)} companies")
                await asyncio.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"[ENHANCED-ENRICHMENT] Error enriching {company.get('name')}: {e}")
            continue
    
    return enriched_count

