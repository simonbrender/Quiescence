"""
Celerio Scout - Portfolio Scraper Integration
Scrapes VC portfolios and integrates with main system
"""
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Set
import re
import aiohttp
from urllib.parse import urlparse, urljoin

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

from bs4 import BeautifulSoup


class PortfolioScraper:
    """Scrapes VC portfolio pages and extracts company information"""
    
    def __init__(self):
        self.seed_data_path = Path("data/seed_data.json")
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from a URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove www. prefix
            domain = domain.replace('www.', '')
            # Remove trailing slashes and paths
            domain = domain.split('/')[0]
            if domain and '.' in domain:
                return domain.lower()
        except:
            pass
        return None
    
    async def _validate_domain(self, domain: str) -> bool:
        """Validate that a domain exists and is reachable"""
        if not domain or len(domain) < 3:
            return False
        
        # Quick format check first
        if '.' not in domain or len(domain.split('.')) < 2:
            return False
        
        try:
            session = await self._get_session()
            # Try https first (most common)
            try:
                async with session.get(
                    f"https://{domain}",
                    timeout=aiohttp.ClientTimeout(total=3),
                    allow_redirects=True,
                    ssl=False
                ) as response:
                    if response.status < 400:
                        return True
            except:
                # Try http as fallback
                try:
                    async with session.get(
                        f"http://{domain}",
                        timeout=aiohttp.ClientTimeout(total=3),
                        allow_redirects=True
                    ) as response:
                        if response.status < 400:
                            return True
                except:
                    pass
        except Exception:
            # If validation fails, we'll still try the domain
            pass
        return False
    
    async def _discover_domain_from_name(self, company_name: str) -> Optional[str]:
        """Try to discover domain from company name using multiple heuristics"""
        if not company_name or len(company_name) < 2:
            return None
        
        # Clean company name - remove special chars but keep hyphens/spaces for now
        clean_name = re.sub(r'[^\w\s-]', '', company_name.lower().strip())
        # Remove extra spaces but keep single spaces/hyphens
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Generate potential domains in order of likelihood
        potential_domains = []
        
        # Strategy 1: Direct name with .com (most common)
        no_spaces = clean_name.replace(' ', '').replace('-', '')
        potential_domains.append(f"{no_spaces}.com")
        
        # Strategy 2: With hyphens (common for multi-word companies)
        with_hyphens = clean_name.replace(' ', '-')
        potential_domains.append(f"{with_hyphens}.com")
        
        # Strategy 3: Common TLDs for startups
        for tld in ['.io', '.ai', '.co']:
            potential_domains.append(f"{no_spaces}{tld}")
            potential_domains.append(f"{with_hyphens}{tld}")
        
        # Strategy 4: Less common TLDs
        for tld in ['.app', '.tech', '.dev']:
            potential_domains.append(f"{no_spaces}{tld}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_domains = []
        for domain in potential_domains:
            if domain not in seen:
                seen.add(domain)
                unique_domains.append(domain)
        
        # Try validating domains (limit to top 8 to avoid too many requests)
        for domain in unique_domains[:8]:
            if await self._validate_domain(domain):
                return domain
        
        # If validation fails, return the most likely candidate anyway (.com)
        # This allows the system to try analyzing it even if validation was slow/failed
        return f"{no_spaces}.com" if no_spaces else None
    
    def get_available_portfolios(self, db_conn=None) -> List[Dict]:
        """Get list of available portfolios from database or seed data"""
        portfolios = []
        
        # Try database first
        if db_conn:
            try:
                results = db_conn.execute("SELECT * FROM vcs ORDER BY firm_name").fetchall()
                columns = [desc[0] for desc in db_conn.description]
                
                for row in results:
                    vc_dict = dict(zip(columns, row))
                    focus_areas = []
                    if vc_dict.get('focus_areas'):
                        try:
                            focus_areas = json.loads(vc_dict['focus_areas'])
                        except:
                            focus_areas = [vc_dict['focus_areas']] if vc_dict['focus_areas'] else []
                    
                    portfolios.append({
                        'firm_name': vc_dict['firm_name'],
                        'url': vc_dict['url'],
                        'domain': vc_dict.get('domain', ''),
                        'type': vc_dict.get('type', 'VC'),
                        'stage': vc_dict.get('stage', 'Unknown'),
                        'focus_areas': focus_areas,
                        'portfolio_url': vc_dict.get('portfolio_url', vc_dict['url'])
                    })
                
                if portfolios:
                    return portfolios
            except Exception as e:
                print(f"Error loading portfolios from database: {e}")
        
        # Fallback to seed data
        if self.seed_data_path.exists():
            with open(self.seed_data_path, 'r') as f:
                seed_data = json.load(f)
            return seed_data.get('vcs', [])
        
        return []
    
    async def scrape_portfolio(self, firm_name: str, url: str, firm_type: str = "VC") -> List[Dict]:
        """
        Scrape a single portfolio page
        Returns list of company dictionaries
        
        Strategy:
        1. Try Playwright browser automation (best for JavaScript-heavy sites)
        2. Fall back to crawl4ai if Playwright unavailable
        3. Fall back to HTTP requests if both fail
        """
        companies = []
        html_content = None
        technical_details = {}
        
        # Strategy 1: Try Playwright browser automation (most reliable for JS-heavy sites)
        if PLAYWRIGHT_AVAILABLE and BrowserScraper:
            try:
                print(f"Using Playwright browser automation for {firm_name}...")
                # Determine wait selectors based on firm
                wait_selectors = []
                if firm_name == "Y Combinator":
                    wait_selectors = ['.company-card', '[class*="Company"]', 'a[href*="/companies/"]']
                elif firm_name == "Antler":
                    wait_selectors = ['.portfolio-item', '[class*="company"]']
                elif firm_name == "NFX":
                    wait_selectors = ['.company', '[class*="portfolio"]']
                
                async with BrowserScraper() as browser_scraper:
                    result = await browser_scraper.scrape_with_browser(
                        url=url,
                        wait_selectors=wait_selectors if wait_selectors else None,
                        wait_timeout=60000,
                        extract_technical_details=True
                    )
                    
                    if result.get('success') and result.get('companies'):
                        companies = result['companies']
                        html_content = result.get('html')
                        technical_details = result.get('technical_details', {})
                        print(f"Playwright extracted {len(companies)} companies from {firm_name}")
                        print(f"Technical details: Framework={technical_details.get('framework')}, "
                              f"Rendering={technical_details.get('rendering_method')}")
                        
                        # Ensure all companies have domains using discovery
                        for company in companies:
                            if not company.get('domain'):
                                domain = await self._discover_domain_from_name(company.get('name', ''))
                                if domain:
                                    company['domain'] = domain
                                    print(f"Discovered domain for {company.get('name')}: {domain}")
                        
                        # If we got companies, return them (don't need to parse HTML)
                        if companies:
                            return companies
            except Exception as e:
                print(f"Playwright error for {firm_name}: {e}, trying crawl4ai...")
        
        # Strategy 2: Try crawl4ai (for JavaScript-heavy sites)
        if CRAWL4AI_AVAILABLE and not companies:
            try:
                browser_config = BrowserConfig(
                    headless=True,
                    verbose=False
                )
                
                crawler_config = CrawlerRunConfig(
                    wait_for_images=False,
                    process_iframes=False,
                    screenshot=False,
                    wait_for="domcontentloaded",  # Faster than networkidle
                    page_timeout=60000  # 60 seconds
                )
                
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result = await crawler.arun(url=url, config=crawler_config)
                    
                    if result.success and result.html:
                        html_content = result.html
            except Exception as e:
                print(f"Crawl4AI error for {firm_name}: {e}, trying fallback...")
        
        # Fallback to regular HTTP request if crawl4ai failed or unavailable
        if not html_content:
            try:
                session = await self._get_session()
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5'
                }
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True) as response:
                    if response.status == 200:
                        html_content = await response.text(encoding='utf-8', errors='ignore')
                    elif response.status == 404:
                        # Try alternative URLs for known VCs
                        print(f"404 for {firm_name} at {url}, trying alternatives...")
                        alternative_urls = {
                            'NFX': ['https://www.nfx.com/', 'https://www.nfx.com/companies'],
                            'Y Combinator': ['https://www.ycombinator.com/companies'],
                        }
                        if firm_name in alternative_urls:
                            for alt_url in alternative_urls[firm_name]:
                                try:
                                    async with session.get(alt_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as alt_resp:
                                        if alt_resp.status == 200:
                                            html_content = await alt_resp.text(encoding='utf-8', errors='ignore')
                                            print(f"Found content at {alt_url}")
                                            break
                                except:
                                    continue
                        if not html_content:
                            print(f"HTTP error {response.status} for {firm_name} - no alternatives worked")
                            return []
                    else:
                        print(f"HTTP error {response.status} for {firm_name}")
                        return []
            except Exception as e:
                print(f"Error fetching {firm_name}: {e}")
                return []
        
        # Parse HTML and extract companies
        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Special handling for known portfolio structures
                if firm_name == "Y Combinator":
                    # Try using the existing YC batch scraper first (more reliable)
                    try:
                        from osint_sources import scrape_yc_batch
                        # Extract batch from URL or use recent batches
                        batch_match = re.search(r'batch=([WS]\d+)', url)
                        if batch_match:
                            batch = batch_match.group(1)
                            print(f"Using YC batch scraper for batch {batch}")
                            batch_companies = await scrape_yc_batch(batch)
                            if batch_companies:
                                companies = batch_companies
                            else:
                                companies = await self._scrape_yc_portfolio(soup, url)
                        else:
                            # Try multiple recent batches
                            print("Scraping multiple YC batches...")
                            recent_batches = ['W24', 'S24', 'W23', 'S23', 'W22', 'S22']
                            all_companies = []
                            for batch in recent_batches[:3]:  # Limit to 3 batches
                                try:
                                    batch_companies = await scrape_yc_batch(batch)
                                    all_companies.extend(batch_companies)
                                except:
                                    continue
                            if all_companies:
                                companies = all_companies
                            else:
                                companies = await self._scrape_yc_portfolio(soup, url)
                    except Exception as e:
                        print(f"YC batch scraper failed, using fallback: {e}")
                        companies = await self._scrape_yc_portfolio(soup, url)
                elif firm_name == "NFX":
                    companies = await self._scrape_nfx_portfolio(soup, url)
                elif firm_name == "Antler":
                    companies = await self._scrape_antler_portfolio(soup, url)
                else:
                    # Generic scraping for other portfolios
                    companies = await self._scrape_generic_portfolio(soup, url, firm_name)
            except Exception as e:
                print(f"Error parsing HTML for {firm_name}: {e}")
                return []
        
        return companies
    
    async def _scrape_yc_portfolio(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Scrape Y Combinator portfolio - improved extraction"""
        companies = []
        seen_companies = set()
        
        print(f"Scraping YC portfolio from {url}")
        
        # YC uses React, so we need to look for various patterns
        # Strategy 1: Look for company links with /companies/ pattern
        company_links = soup.find_all('a', href=re.compile(r'/companies/[^/]+'))
        
        # Strategy 2: Look for data attributes that might contain company info
        company_elements = soup.find_all(['div', 'article', 'li'], 
            attrs={'data-company': True, 'data-name': True, 'class': re.compile(r'company|startup', re.I)})
        
        # Strategy 3: Look for text patterns that indicate company names
        # YC often has company names in specific divs/spans
        potential_companies = soup.find_all(['div', 'span', 'h3', 'h4'], 
            class_=re.compile(r'company-name|startup-name|name', re.I))
        
        # Strategy 4: Extract from JSON-LD or script tags (YC might embed data)
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'itemListElement' in data:
                    for item in data.get('itemListElement', []):
                        if 'name' in item:
                            company_name = item['name']
                            domain = item.get('url', '').replace('https://', '').replace('http://', '').split('/')[0]
                            if company_name and company_name.lower() not in seen_companies:
                                seen_companies.add(company_name.lower())
                                companies.append({
                                    'name': company_name,
                                    'domain': domain or '',
                                    'source': 'yc',
                                    'yc_batch': '',
                                    'portfolio_url': url
                                })
            except:
                pass
        
        # Process company links
        for link in company_links[:500]:  # Increased limit for YC
            try:
                href = link.get('href', '')
                company_name = link.get_text(strip=True)
                
                # Skip if no name or too short
                if not company_name or len(company_name) < 2:
                    # Try to get name from title or aria-label
                    company_name = link.get('title', '') or link.get('aria-label', '')
                    if not company_name or len(company_name) < 2:
                        continue
                
                # Skip duplicates
                name_key = company_name.lower().strip()
                if name_key in seen_companies:
                    continue
                seen_companies.add(name_key)
                
                # Extract domain - YC company pages have the domain in the URL or page
                domain = None
                
                # Try to extract from href (YC format: /companies/company-name)
                if '/companies/' in href:
                    # Visit the company page to get domain
                    company_page_url = urljoin('https://www.ycombinator.com', href)
                    try:
                        session = await self._get_session()
                        async with session.get(company_page_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                            if resp.status == 200:
                                page_content = await resp.text()
                                page_soup = BeautifulSoup(page_content, 'html.parser')
                                # Look for external website link
                                website_links = page_soup.find_all('a', href=re.compile(r'^https?://'))
                                for wlink in website_links:
                                    wtext = wlink.get_text(strip=True).lower()
                                    if 'website' in wtext or 'visit' in wtext or wlink.get('href', '').startswith('http'):
                                        parsed = await self._extract_domain_from_url(wlink.get('href', ''))
                                        if parsed and parsed not in ['ycombinator.com', 'www.ycombinator.com']:
                                            domain = parsed
                                            break
                    except:
                        pass
                
                # Extract batch from URL
                yc_batch = ''
                batch_match = re.search(r'batch=([WS]\d+)', url)
                if batch_match:
                    yc_batch = batch_match.group(1)
                
                # Look for domain in parent elements
                if not domain:
                    parent = link.find_parent(['div', 'article', 'li', 'section'])
                    if parent:
                        # Look for domain patterns in text
                        parent_text = parent.get_text()
                        domain_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9-]*\.(?:com|io|ai|co|dev|app|tech|org))', parent_text)
                        if domain_match:
                            domain = domain_match.group(1).lower()
                
                # Discover domain if still not found
                if not domain:
                    domain = await self._discover_domain_from_name(company_name)
                
                if company_name:
                    companies.append({
                        'name': company_name.strip(),
                        'domain': domain or '',
                        'source': 'yc',
                        'yc_batch': yc_batch,
                        'portfolio_url': url
                    })
            except Exception as e:
                print(f"Error processing YC company link: {e}")
                continue
        
        # Process potential company elements
        for elem in list(company_elements) + list(potential_companies)[:200]:
            try:
                company_name = None
                if elem.get('data-company'):
                    company_name = elem.get('data-company')
                elif elem.get('data-name'):
                    company_name = elem.get('data-name')
                else:
                    company_name = elem.get_text(strip=True)
                
                if not company_name or len(company_name) < 2:
                    continue
                
                name_key = company_name.lower().strip()
                if name_key in seen_companies:
                    continue
                seen_companies.add(name_key)
                
                # Try to find domain nearby
                domain = None
                parent = elem.find_parent(['div', 'article', 'li'])
                if parent:
                    # Look for links
                    links = parent.find_all('a', href=re.compile(r'^https?://'))
                    for link in links:
                        parsed = await self._extract_domain_from_url(link.get('href', ''))
                        if parsed and parsed not in ['ycombinator.com', 'www.ycombinator.com']:
                            domain = parsed
                            break
                
                if not domain:
                    domain = await self._discover_domain_from_name(company_name)
                
                companies.append({
                    'name': company_name.strip(),
                    'domain': domain or '',
                    'source': 'yc',
                    'yc_batch': '',
                    'portfolio_url': url
                })
            except:
                continue
        
        # If still no companies found, try a more aggressive approach
        if len(companies) == 0:
            print("Trying alternative YC scraping approach...")
            # Look for any text that might be company names
            # YC pages often have company names in various formats
            all_text_elements = soup.find_all(['span', 'div', 'a', 'h3', 'h4'], 
                string=re.compile(r'[A-Z][a-z]+'))
            
            for elem in all_text_elements[:500]:  # Limit search
                text = elem.get_text(strip=True)
                if not text or len(text) < 3 or len(text) > 50:
                    continue
                
                # Skip common non-company text
                skip_patterns = ['y combinator', 'batch', 'apply', 'learn', 'read', 'view', 'more', 
                               'companies', 'portfolio', 'about', 'contact', 'blog', 'news']
                if any(pattern in text.lower() for pattern in skip_patterns):
                    continue
                
                # Check if this looks like a company name (starts with capital, reasonable length)
                if text[0].isupper() and not text.lower() in seen_companies:
                    # Try to find associated domain
                    parent = elem.find_parent(['div', 'article', 'li', 'section'])
                    domain = None
                    if parent:
                        links = parent.find_all('a', href=re.compile(r'^https?://'))
                        for link in links:
                            href = link.get('href', '')
                            parsed = await self._extract_domain_from_url(href)
                            if parsed and parsed not in ['ycombinator.com', 'www.ycombinator.com']:
                                domain = parsed
                                break
                    
                    if not domain:
                        domain = await self._discover_domain_from_name(text)
                    
                    seen_companies.add(text.lower())
                    companies.append({
                        'name': text,
                        'domain': domain or '',
                        'source': 'yc',
                        'yc_batch': '',
                        'portfolio_url': url
                    })
        
        print(f"Found {len(companies)} companies from YC")
        return companies
    
    async def _scrape_nfx_portfolio(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Scrape NFX portfolio - improved extraction"""
        companies = []
        seen_companies = set()
        
        print(f"Scraping NFX portfolio from {url}")
        
        # NFX homepage has companies listed - look for various patterns
        # Strategy 1: Look for company cards/elements
        company_elements = soup.find_all(['a', 'div', 'article', 'section'], 
            class_=re.compile(r'company|portfolio|startup|card|investment', re.I))
        
        # Strategy 2: Look for all external links (NFX companies link to their websites)
        all_links = soup.find_all('a', href=re.compile(r'^https?://'))
        
        # Strategy 3: Look for company names in headings
        company_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], 
            class_=re.compile(r'company|startup|name', re.I))
        
        # Strategy 4: Look for data attributes
        data_companies = soup.find_all(attrs={'data-company': True, 'data-name': True})
        
        # Process all potential company elements
        all_elements = list(company_elements) + list(all_links)[:300] + list(company_headings) + list(data_companies)
        
        for elem in all_elements:
            try:
                company_name = None
                domain = None
                
                # Extract company name from various sources
                if elem.get('data-company'):
                    company_name = elem.get('data-company')
                elif elem.get('data-name'):
                    company_name = elem.get('data-name')
                else:
                    # Try to find name in child elements
                    name_elem = elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'p'], 
                        class_=re.compile(r'name|title|company-name|startup-name', re.I))
                    if name_elem:
                        company_name = name_elem.get_text(strip=True)
                    elif elem.name == 'a':
                        company_name = elem.get_text(strip=True)
                        # Check if link is external company website
                        href = elem.get('href', '')
                        if href.startswith('http'):
                            parsed_domain = await self._extract_domain_from_url(href)
                            if parsed_domain and parsed_domain not in ['nfx.com', 'www.nfx.com']:
                                domain = parsed_domain
                                # Company name might be in title or aria-label
                                if not company_name or len(company_name) < 2:
                                    company_name = elem.get('title', '') or elem.get('aria-label', '')
                    elif elem.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                        company_name = elem.get_text(strip=True)
                
                # Skip if no name or too short
                if not company_name or len(company_name) < 2:
                    continue
                
                # Skip common non-company text
                skip_terms = ['learn more', 'read more', 'view', 'visit', 'website', 'apply', 'join', 'nfx', 'portfolio', 
                             'raises', 'series', 'funding', 'million', 'billion', 'investors', 'kenya', 'nigeria', 'singapore',
                             'london', 'new york', 'san francisco', 'menap', 'europe', 'asia', 'africa', 'americas']
                if any(term in company_name.lower() for term in skip_terms):
                    continue
                
                # Skip if looks like a news headline (contains "raises", "announces", etc.)
                headline_indicators = ['raises', 'announces', 'secures', 'closes', 'led by', 'invests in']
                if any(indicator in company_name.lower() for indicator in headline_indicators):
                    continue
                
                # Skip if too long (likely a headline or description)
                if len(company_name) > 80:
                    continue
                
                # Skip duplicates
                name_key = company_name.lower().strip()
                if name_key in seen_companies:
                    continue
                seen_companies.add(name_key)
                
                # Look for domain in parent elements
                if not domain:
                    parent = elem.find_parent(['div', 'article', 'li', 'section', 'card'])
                    if parent:
                        # Look for external links
                        external_links = parent.find_all('a', href=re.compile(r'^https?://'))
                        for ext_link in external_links:
                            ext_href = ext_link.get('href', '')
                            parsed_domain = await self._extract_domain_from_url(ext_href)
                            if parsed_domain and parsed_domain not in ['nfx.com', 'www.nfx.com']:
                                domain = parsed_domain
                                break
                        
                        # Also look for domain in text
                        if not domain:
                            parent_text = parent.get_text()
                            domain_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9-]*\.(?:com|io|ai|co|dev|app|tech))', parent_text)
                            if domain_match:
                                potential_domain = domain_match.group(1).lower()
                                if 'nfx' not in potential_domain:
                                    domain = potential_domain
                
                # Discover domain if needed
                if not domain:
                    domain = await self._discover_domain_from_name(company_name)
                
                if company_name:
                    companies.append({
                        'name': company_name.strip(),
                        'domain': domain or '',
                        'source': 'nfx',
                        'yc_batch': '',
                        'portfolio_url': url
                    })
            except Exception as e:
                print(f"Error processing NFX company element: {e}")
                continue
        
        print(f"Found {len(companies)} companies from NFX")
        return companies
    
    async def _scrape_antler_portfolio(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Scrape Antler portfolio - improved extraction"""
        companies = []
        seen_companies = set()
        
        print(f"Scraping Antler portfolio from {url}")
        
        # Antler uses JavaScript-rendered content, so crawl4ai should have rendered it
        # Strategy 1: Look for company cards/elements
        company_elements = soup.find_all(['a', 'div', 'article', 'li'], 
            class_=re.compile(r'company|portfolio|startup|card|founder', re.I))
        
        # Strategy 2: Look for all external links (Antler companies link to their websites)
        all_links = soup.find_all('a', href=re.compile(r'^https?://'))
        
        # Strategy 3: Look for company names in headings and text
        company_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], 
            class_=re.compile(r'company|startup|name', re.I))
        
        # Process company elements
        for elem in list(company_elements) + list(all_links)[:300]:
            try:
                company_name = None
                domain = None
                
                # Extract company name
                name_elem = elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div'], 
                    class_=re.compile(r'name|title|company-name|startup-name', re.I))
                if name_elem:
                    company_name = name_elem.get_text(strip=True)
                elif elem.name == 'a':
                    company_name = elem.get_text(strip=True)
                    # Check if link is external company website
                    href = elem.get('href', '')
                    if href.startswith('http'):
                        parsed_domain = await self._extract_domain_from_url(href)
                        if parsed_domain and parsed_domain not in ['antler.co', 'www.antler.co', 'antler.com']:
                            domain = parsed_domain
                            # Company name might be in title or aria-label
                            if not company_name or len(company_name) < 2:
                                company_name = elem.get('title', '') or elem.get('aria-label', '')
                
                # Skip if no name or too short
                if not company_name or len(company_name) < 2:
                    continue
                
                # Skip common non-company text
                skip_terms = ['learn more', 'read more', 'view', 'visit', 'website', 'apply', 'join', 'antler',
                             'raises', 'series', 'funding', 'million', 'billion', 'investors', 'kenya', 'nigeria', 
                             'singapore', 'london', 'new york', 'san francisco', 'menap', 'europe', 'asia', 'africa']
                if any(term in company_name.lower() for term in skip_terms):
                    continue
                
                # Skip if looks like a news headline
                headline_indicators = ['raises', 'announces', 'secures', 'closes', 'led by', 'invests in']
                if any(indicator in company_name.lower() for indicator in headline_indicators):
                    continue
                
                # Skip if too long (likely a headline)
                if len(company_name) > 80:
                    continue
                
                # Skip duplicates
                name_key = company_name.lower().strip()
                if name_key in seen_companies:
                    continue
                seen_companies.add(name_key)
                
                # Look for domain in parent elements
                if not domain:
                    parent = elem.find_parent(['div', 'article', 'li', 'section', 'card'])
                    if parent:
                        # Look for external links
                        external_links = parent.find_all('a', href=re.compile(r'^https?://'))
                        for ext_link in external_links:
                            ext_href = ext_link.get('href', '')
                            parsed_domain = await self._extract_domain_from_url(ext_href)
                            if parsed_domain and parsed_domain not in ['antler.co', 'www.antler.co', 'antler.com']:
                                domain = parsed_domain
                                break
                        
                        # Also look for domain in text
                        if not domain:
                            parent_text = parent.get_text()
                            domain_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9-]*\.(?:com|io|ai|co|dev|app|tech))', parent_text)
                            if domain_match:
                                potential_domain = domain_match.group(1).lower()
                                if 'antler' not in potential_domain:
                                    domain = potential_domain
                
                # Discover domain if needed
                if not domain:
                    domain = await self._discover_domain_from_name(company_name)
                
                if company_name:
                    companies.append({
                        'name': company_name.strip(),
                        'domain': domain or '',
                        'source': 'antler',
                        'yc_batch': '',
                        'portfolio_url': url
                    })
            except Exception as e:
                print(f"Error processing Antler company element: {e}")
                continue
        
        # Process company headings
        for heading in company_headings[:100]:
            try:
                company_name = heading.get_text(strip=True)
                if not company_name or len(company_name) < 2:
                    continue
                
                name_key = company_name.lower().strip()
                if name_key in seen_companies:
                    continue
                seen_companies.add(name_key)
                
                # Look for domain nearby
                parent = heading.find_parent(['div', 'article', 'li', 'section'])
                domain = None
                if parent:
                    links = parent.find_all('a', href=re.compile(r'^https?://'))
                    for link in links:
                        parsed = await self._extract_domain_from_url(link.get('href', ''))
                        if parsed and parsed not in ['antler.co', 'www.antler.co']:
                            domain = parsed
                            break
                
                if not domain:
                    domain = await self._discover_domain_from_name(company_name)
                
                companies.append({
                    'name': company_name.strip(),
                    'domain': domain or '',
                    'source': 'antler',
                    'yc_batch': '',
                    'portfolio_url': url
                })
            except:
                continue
        
        print(f"Found {len(companies)} companies from Antler")
        return companies
    
    async def _scrape_generic_portfolio(self, soup: BeautifulSoup, url: str, firm_name: str) -> List[Dict]:
        """Generic portfolio scraping with domain extraction"""
        companies = []
        seen_companies = set()
        
        # Extract base domain to exclude internal links
        base_domain = await self._extract_domain_from_url(url)
        
        # Look for common patterns
        company_elements = soup.find_all(['a', 'div', 'li', 'article'], 
            attrs={'data-company': True, 'data-name': True, 'class': re.compile(r'company|portfolio|startup|card', re.I)})
        
        # Look for portfolio/company links
        potential_links = soup.find_all('a', href=re.compile(r'/company|/portfolio|/startup|/companies', re.I))
        
        # Look for all external links (might be company websites)
        external_links = soup.find_all('a', href=re.compile(r'^https?://'))
        
        all_elements = list(company_elements) + list(potential_links) + list(external_links)[:300]
        
        for elem in all_elements:
            company_name = None
            domain = None
            
            # Extract company name from various sources
            if elem.get('data-company'):
                company_name = elem.get('data-company')
            elif elem.get('data-name'):
                company_name = elem.get('data-name')
            elif elem.name == 'a':
                company_name = elem.get_text(strip=True)
                # Skip common link text
                if company_name.lower() in ['learn more', 'view', 'read more', 'visit', 'website', 'homepage']:
                    continue
                # Check if this is an external company link
                href = elem.get('href', '')
                if href.startswith('http'):
                    parsed_domain = await self._extract_domain_from_url(href)
                    if parsed_domain and parsed_domain != base_domain:
                        domain = parsed_domain
            
            # Try to find name in child elements
            if not company_name:
                name_elem = elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div'], 
                    class_=re.compile(r'name|title|company-name', re.I))
                if name_elem:
                    company_name = name_elem.get_text(strip=True)
            
            if not company_name or len(company_name) < 2:
                continue
            
            # Skip duplicates
            name_key = company_name.lower()
            if name_key in seen_companies:
                continue
            seen_companies.add(name_key)
            
            # Look for domain in parent or sibling elements
            if not domain:
                parent = elem.find_parent(['div', 'article', 'li', 'section', 'card'])
                if parent:
                    # Look for external links in parent
                    ext_links = parent.find_all('a', href=re.compile(r'^https?://'))
                    for ext_link in ext_links:
                        ext_href = ext_link.get('href', '')
                        parsed_domain = await self._extract_domain_from_url(ext_href)
                        if parsed_domain and parsed_domain != base_domain:
                            domain = parsed_domain
                            break
                    
                    # Check data attributes for domain
                    if not domain:
                        if parent.get('data-url'):
                            domain = await self._extract_domain_from_url(parent.get('data-url'))
                        elif parent.get('data-website'):
                            domain = await self._extract_domain_from_url(parent.get('data-website'))
            
            # Discover domain from name if still not found
            if not domain:
                domain = await self._discover_domain_from_name(company_name)
            
            if company_name:
                companies.append({
                    'name': company_name,
                    'domain': domain or '',
                    'source': firm_name.lower().replace(' ', '_'),
                    'yc_batch': '',
                    'portfolio_url': url
                })
        
        return companies
    
    async def scrape_multiple_portfolios(self, portfolio_names: List[str]) -> Dict[str, List[Dict]]:
        """
        Scrape multiple portfolios
        Returns dict mapping firm_name -> list of companies
        """
        portfolios = self.get_available_portfolios()
        results = {}
        
        for portfolio in portfolios:
            if portfolio['firm_name'] in portfolio_names:
                print(f"Scraping {portfolio['firm_name']}...")
                companies = await self.scrape_portfolio(
                    portfolio['firm_name'],
                    portfolio.get('portfolio_url', portfolio['url']),
                    portfolio.get('type', 'VC')
                )
                
                # Post-process: ensure all companies have domains
                processed_companies = []
                for company in companies:
                    if not company.get('domain'):
                        # Try to discover domain
                        domain = await self._discover_domain_from_name(company['name'])
                        if domain:
                            company['domain'] = domain
                    
                    # Only include companies with valid domains or names
                    if company.get('domain') or company.get('name'):
                        processed_companies.append(company)
                
                results[portfolio['firm_name']] = processed_companies
                print(f"Found {len(processed_companies)} companies from {portfolio['firm_name']}")
        
        return results
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

