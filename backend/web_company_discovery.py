"""
Web Company Discovery for Free-Text Queries
Discovers companies from web sources based on search criteria
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, quote_plus
import json
from datetime import datetime

# Try to import crawl4ai for advanced web scraping
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

try:
    from browser_scraper import BrowserScraper
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    BrowserScraper = None


class WebCompanyDiscovery:
    """Discovers companies from web sources based on search criteria"""
    
    def __init__(self, progress_callback=None):
        self.session = None
        self.progress_callback = progress_callback
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def discover_companies(self, parsed_params: Dict, progress_callback=None) -> List[Dict]:
        """
        Discover companies from web sources based on parsed search parameters.
        
        Args:
            parsed_params: Dictionary with search criteria (stages, focus_areas, etc.)
        
        Returns:
            List of discovered company dictionaries
        """
        print(f"[WEB-DISCOVERY] Starting discovery with params: {parsed_params}")
        discovered = []
        
        # Check if this is a portfolio query
        if parsed_params.get('is_portfolio_query') and parsed_params.get('portfolio_sources'):
            print(f"[WEB-DISCOVERY] Detected portfolio query for sources: {parsed_params['portfolio_sources']}")
            if self.progress_callback:
                self.progress_callback({
                    'type': 'portfolio_scraping_started',
                    'sources': parsed_params['portfolio_sources'],
                    'message': f"Starting portfolio scraping for: {', '.join(parsed_params['portfolio_sources'])}",
                    'timestamp': datetime.now().isoformat()
                })
            portfolio_companies = await self._scrape_portfolios(parsed_params['portfolio_sources'], progress_callback=self.progress_callback or progress_callback)
            discovered.extend(portfolio_companies)
            print(f"[WEB-DISCOVERY] Found {len(portfolio_companies)} companies from portfolios")
            if self.progress_callback:
                self.progress_callback({
                    'type': 'portfolio_scraping_complete',
                    'companies_found': len(portfolio_companies),
                    'message': f'Portfolio scraping completed: {len(portfolio_companies)} companies found',
                    'timestamp': datetime.now().isoformat()
                })
            return discovered
        
        # Build search query from parsed parameters
        search_terms = []
        if parsed_params.get('focus_areas'):
            search_terms.extend(parsed_params['focus_areas'])
        if parsed_params.get('stages'):
            search_terms.extend(parsed_params['stages'])
        if parsed_params.get('keywords'):
            search_terms.extend(parsed_params['keywords'])
        
        if not search_terms:
            # Fallback: use generic startup search
            search_terms = ['startup', 'company']
        
        print(f"[WEB-DISCOVERY] Search terms: {search_terms}")
        
        # Search multiple sources
        tasks = []
        
        # 1. Crunchbase search
        if parsed_params.get('stages') or parsed_params.get('focus_areas'):
            print(f"[WEB-DISCOVERY] Queuing Crunchbase search...")
            tasks.append(self._search_crunchbase(parsed_params))
        
        # 2. Web search (via DuckDuckGo)
        search_query = ' '.join(search_terms[:3])  # Use first 3 terms
        print(f"[WEB-DISCOVERY] Queuing web search for: {search_query}")
        tasks.append(self._search_web(search_query, parsed_params))
        
        # 3. LinkedIn company search (placeholder)
        if parsed_params.get('focus_areas'):
            print(f"[WEB-DISCOVERY] Queuing LinkedIn search...")
            tasks.append(self._search_linkedin_companies(parsed_params))
        
        # Run all searches concurrently with progress tracking
        print(f"[WEB-DISCOVERY] Running {len(tasks)} search tasks concurrently...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and track progress
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[WEB-DISCOVERY] Search task {idx+1} failed: {result}")
            elif isinstance(result, list):
                print(f"[WEB-DISCOVERY] Search task {idx+1} found {len(result)} companies")
        
        # Combine and deduplicate results
        seen_domains = set()
        for result_list in results:
            if isinstance(result_list, list):
                for company in result_list:
                    domain = company.get('domain', '').lower().strip()
                    if domain and domain not in seen_domains and len(domain) > 3:  # Basic validation
                        seen_domains.add(domain)
                        discovered.append(company)
        
        print(f"[WEB-DISCOVERY] Total unique companies discovered: {len(discovered)}")
        return discovered
    
    async def _search_crunchbase(self, params: Dict) -> List[Dict]:
        """Search Crunchbase for companies matching criteria"""
        companies = []
        try:
            # Build Crunchbase search URL
            search_terms = []
            if params.get('focus_areas'):
                search_terms.extend(params['focus_areas'][:2])
            if params.get('stages'):
                search_terms.extend(params['stages'][:1])
            
            if not search_terms:
                return companies
            
            query = ' '.join(search_terms)
            # Note: Crunchbase requires authentication for API access
            # This is a placeholder for web scraping approach
            url = f"https://www.crunchbase.com/discover/organization.companies/{quote_plus(query)}"
            
            session = await self._get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract company links (Crunchbase structure)
                    company_links = soup.find_all('a', href=re.compile(r'/organization/'))
                    for link in company_links[:20]:  # Limit to 20 results
                        company_name = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        if company_name and href:
                            # Extract domain from Crunchbase profile
                            domain = await self._extract_domain_from_crunchbase(href)
                            if domain:
                                companies.append({
                                    'name': company_name,
                                    'domain': domain,
                                    'source': 'crunchbase',
                                    'last_raise_stage': params.get('stages', [None])[0] if params.get('stages') else None,
                                    'focus_areas': params.get('focus_areas', [])
                                })
        except Exception as e:
            print(f"Crunchbase search error: {e}")
        
        return companies
    
    async def _extract_domain_from_crunchbase(self, profile_url: str) -> Optional[str]:
        """Extract company domain from Crunchbase profile"""
        try:
            full_url = f"https://www.crunchbase.com{profile_url}" if not profile_url.startswith('http') else profile_url
            session = await self._get_session()
            async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for website link
                    website_link = soup.find('a', href=re.compile(r'^https?://'))
                    if website_link:
                        href = website_link.get('href', '')
                        parsed = urlparse(href)
                        return parsed.netloc.replace('www.', '')
        except Exception as e:
            print(f"Error extracting domain from Crunchbase: {e}")
        return None
    
    async def _search_web(self, query: str, params: Dict) -> List[Dict]:
        """Search web using DuckDuckGo or similar"""
        companies = []
        try:
            # Use DuckDuckGo HTML search (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query + ' startup company')}"
            
            session = await self._get_session()
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract results
                    results = soup.find_all('a', class_=re.compile(r'result'))
                    for result in results[:15]:  # Limit to 15 results
                        title = result.get_text(strip=True)
                        href = result.get('href', '')
                        
                        if title and href:
                            parsed = urlparse(href)
                            domain = parsed.netloc.replace('www.', '')
                            
                            # Filter by focus areas if specified
                            if params.get('focus_areas'):
                                title_lower = title.lower()
                                if any(area.lower() in title_lower for area in params['focus_areas']):
                                    companies.append({
                                        'name': title,
                                        'domain': domain,
                                        'source': 'web_search',
                                        'focus_areas': params.get('focus_areas', [])
                                    })
                            else:
                                companies.append({
                                    'name': title,
                                    'domain': domain,
                                    'source': 'web_search'
                                })
        except Exception as e:
            print(f"Web search error: {e}")
        
        return companies
    
    async def _search_linkedin_companies(self, params: Dict) -> List[Dict]:
        """Search LinkedIn for companies (requires authentication)"""
        # Placeholder - LinkedIn requires OAuth2
        # Could use LinkedIn's public company pages if available
        return []
    
    async def _scrape_portfolios(self, sources: List[str], progress_callback=None) -> List[Dict]:
        """Scrape portfolios from specified sources (YC, Antler, etc.)"""
        companies = []
        
        try:
            # Use observable scraper if progress callback provided, otherwise use enhanced scraper
            if progress_callback:
                from portfolio_scraper_observable import ObservablePortfolioScraper
                scraper = ObservablePortfolioScraper(progress_callback=progress_callback)
                
                if 'yc' in sources and 'antler' in sources:
                    print("[WEB-DISCOVERY] Scraping both YC and Antler portfolios with observability...")
                    results = await scraper.scrape_both_observable()
                    companies.extend(results.get('yc', []))
                    companies.extend(results.get('antler', []))
                elif 'yc' in sources:
                    print("[WEB-DISCOVERY] Scraping YC portfolio with observability...")
                    yc_companies = await scraper.scrape_yc_portfolio_observable()
                    companies.extend(yc_companies)
                elif 'antler' in sources:
                    print("[WEB-DISCOVERY] Scraping Antler portfolio with observability...")
                    antler_companies = await scraper.scrape_antler_portfolio_observable()
                    companies.extend(antler_companies)
            else:
                from portfolio_scraper_enhanced import EnhancedPortfolioScraper
                scraper = EnhancedPortfolioScraper()
                
                if 'yc' in sources and 'antler' in sources:
                    print("[WEB-DISCOVERY] Scraping both YC and Antler portfolios...")
                    results = await scraper.scrape_both_portfolios()
                    companies.extend(results.get('yc', []))
                    companies.extend(results.get('antler', []))
                elif 'yc' in sources:
                    print("[WEB-DISCOVERY] Scraping YC portfolio...")
                    yc_companies = await scraper.scrape_yc_portfolio()
                    companies.extend(yc_companies)
                elif 'antler' in sources:
                    print("[WEB-DISCOVERY] Scraping Antler portfolio...")
                    antler_companies = await scraper.scrape_antler_portfolio()
                    companies.extend(antler_companies)
            
        except Exception as e:
            print(f"[WEB-DISCOVERY] Error scraping portfolios: {e}")
            import traceback
            traceback.print_exc()
        
        return companies
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

