"""
Enhanced Portfolio Scraper with Scroll and Click Support
Generic scraper that adapts to different portfolio websites
"""
import asyncio
import json
from typing import List, Dict, Optional, Set, Callable
import re
from urllib.parse import urlparse
from datetime import datetime

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from bs4 import BeautifulSoup


class PortfolioConfig:
    """Configuration for a portfolio site"""
    def __init__(
        self,
        name: str,
        url: str,
        scroll_type: str = "infinite",  # "infinite" or "load_more"
        company_selectors: List[str] = None,
        load_more_selectors: List[str] = None,
        exclude_domains: List[str] = None,
        max_companies: int = 10000,
        scroll_wait_time: float = 2.0,
        load_more_wait_time: float = 2.0,
        max_scroll_attempts: int = 500,
        max_no_change_count: int = 5,
        extract_company_data: Optional[Callable] = None
    ):
        self.name = name
        self.url = url
        self.scroll_type = scroll_type  # "infinite" or "load_more"
        self.company_selectors = company_selectors or []
        self.load_more_selectors = load_more_selectors or []
        self.exclude_domains = exclude_domains or []
        self.max_companies = max_companies
        self.scroll_wait_time = scroll_wait_time
        self.load_more_wait_time = load_more_wait_time
        self.max_scroll_attempts = max_scroll_attempts
        self.max_no_change_count = max_no_change_count
        self.extract_company_data = extract_company_data


class EnhancedPortfolioScraper:
    """Enhanced portfolio scraper with scroll and click support - generic and adaptable"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def scrape_portfolio(self, config: PortfolioConfig) -> List[Dict]:
        """
        Generic portfolio scraper that adapts to different sites
        
        Args:
            config: PortfolioConfig with site-specific settings
        
        Returns:
            List of discovered company dictionaries
        """
        companies = []
        seen_domains = set()
        seen_names = set()
        
        print(f"[PORTFOLIO-SCRAPER] Starting {config.name} portfolio scrape from {config.url}")
        
        if not PLAYWRIGHT_AVAILABLE:
            print(f"[PORTFOLIO-SCRAPER] ERROR: Playwright not available. Cannot scrape {config.name}.")
            return []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set viewport
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Navigate to portfolio page
                print(f"[PORTFOLIO-SCRAPER] Navigating to {config.name} portfolio page...")
                await page.goto(config.url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2)  # Wait for initial load
                
                if config.scroll_type == "infinite":
                    companies = await self._scrape_infinite_scroll(page, config, seen_domains, seen_names)
                elif config.scroll_type == "load_more":
                    companies = await self._scrape_load_more(page, config, seen_domains, seen_names)
                else:
                    # Single page scrape
                    companies = await self._extract_companies_from_page(page, config, seen_domains, seen_names)
                
                await browser.close()
                
        except Exception as e:
            print(f"[PORTFOLIO-SCRAPER] Error during {config.name} scraping: {e}")
            import traceback
            traceback.print_exc()
        
        # Validate and clean companies
        validated_companies = self._validate_companies(companies, config)
        
        print(f"[PORTFOLIO-SCRAPER] Completed {config.name} scrape: Found {len(validated_companies)} validated companies")
        return validated_companies
    
    async def _scrape_infinite_scroll(
        self, 
        page, 
        config: PortfolioConfig, 
        seen_domains: Set[str], 
        seen_names: Set[str]
    ) -> List[Dict]:
        """Scrape portfolio with infinite scroll"""
        companies = []
        previous_count = 0
        no_change_count = 0
        scroll_attempts = 0
        
        print(f"[PORTFOLIO-SCRAPER] Starting infinite scroll extraction for {config.name}...")
        
        while scroll_attempts < config.max_scroll_attempts and len(companies) < config.max_companies:
            # Extract companies from current page state
            page_companies = await self._extract_companies_from_page(page, config, seen_domains, seen_names)
            
            # Add new companies
            for company in page_companies:
                domain = company.get('domain', '').lower().strip()
                name = company.get('name', '').lower().strip()
                
                if domain:
                    seen_domains.add(domain)
                if name:
                    seen_names.add(name)
                
                companies.append(company)
            
            current_count = len(companies)
            
            # Progress update
            if scroll_attempts % 10 == 0 or current_count != previous_count:
                print(f"[PORTFOLIO-SCRAPER] {config.name}: Extracted {current_count} companies (scroll {scroll_attempts})")
            
            # Check if we're still finding new companies
            if current_count == previous_count:
                no_change_count += 1
                if no_change_count >= config.max_no_change_count:
                    print(f"[PORTFOLIO-SCRAPER] {config.name}: No new companies after {no_change_count} scrolls, stopping...")
                    break
            else:
                no_change_count = 0
            
            previous_count = current_count
            
            # Scroll down
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(config.scroll_wait_time / 2)
            
            # Scroll to bottom to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(config.scroll_wait_time)
            
            scroll_attempts += 1
        
        return companies
    
    async def _scrape_load_more(
        self, 
        page, 
        config: PortfolioConfig, 
        seen_domains: Set[str], 
        seen_names: Set[str]
    ) -> List[Dict]:
        """Scrape portfolio with Load More button"""
        companies = []
        load_more_attempts = 0
        
        print(f"[PORTFOLIO-SCRAPER] Starting Load More extraction for {config.name}...")
        
        while load_more_attempts < config.max_scroll_attempts and len(companies) < config.max_companies:
            # Extract companies from current page state
            page_companies = await self._extract_companies_from_page(page, config, seen_domains, seen_names)
            
            # Add new companies
            for company in page_companies:
                domain = company.get('domain', '').lower().strip()
                name = company.get('name', '').lower().strip()
                
                if domain:
                    seen_domains.add(domain)
                if name:
                    seen_names.add(name)
                
                companies.append(company)
            
            current_count = len(companies)
            
            # Progress update
            if load_more_attempts % 5 == 0:
                print(f"[PORTFOLIO-SCRAPER] {config.name}: Extracted {current_count} companies (Load More attempt {load_more_attempts + 1})")
            
            # Try to find and click Load More button
            load_more_clicked = False
            for selector in config.load_more_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        await button.click()
                        await asyncio.sleep(config.load_more_wait_time)
                        load_more_clicked = True
                        print(f"[PORTFOLIO-SCRAPER] {config.name}: Clicked Load More button")
                        break
                except:
                    continue
            
            # If no button found, scroll to bottom to trigger lazy loading
            if not load_more_clicked:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(config.load_more_wait_time)
                
                # Check again after scroll
                for selector in config.load_more_selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button and await button.is_visible():
                            await button.click()
                            await asyncio.sleep(config.load_more_wait_time)
                            load_more_clicked = True
                            break
                    except:
                        continue
            
            if not load_more_clicked and len(page_companies) == 0:
                print(f"[PORTFOLIO-SCRAPER] {config.name}: No Load More button found and no new companies, stopping...")
                break
            
            load_more_attempts += 1
        
        return companies
    
    async def _extract_companies_from_page(
        self, 
        page, 
        config: PortfolioConfig, 
        seen_domains: Set[str], 
        seen_names: Set[str]
    ) -> List[Dict]:
        """Extract companies from current page state"""
        companies = []
        
        try:
            # Get page HTML
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Use custom extractor if provided
            if config.extract_company_data:
                try:
                    custom_companies = await config.extract_company_data(page, soup, config)
                    companies.extend(custom_companies)
                except Exception as e:
                    print(f"[PORTFOLIO-SCRAPER] Custom extractor error: {e}")
            
            # Generic extraction using selectors
            for selector in config.company_selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        company = await self._extract_company_from_element(elem, config, seen_domains, seen_names)
                        if company:
                            companies.append(company)
                except Exception as e:
                    continue
            
            # Fallback: Generic extraction patterns
            if not companies:
                companies = await self._generic_extraction(soup, config, seen_domains, seen_names)
                
        except Exception as e:
            print(f"[PORTFOLIO-SCRAPER] Error extracting companies from page: {e}")
        
        return companies
    
    async def _extract_company_from_element(
        self, 
        elem, 
        config: PortfolioConfig, 
        seen_domains: Set[str], 
        seen_names: Set[str]
    ) -> Optional[Dict]:
        """Extract company data from a single element"""
        try:
            # Extract company name
            company_name = None
            
            # Try various methods to get name
            name_elem = elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'a'], class_=re.compile(r'name|title|company', re.I))
            if name_elem:
                company_name = name_elem.get_text(strip=True)
            elif elem.name == 'a':
                company_name = elem.get_text(strip=True)
            else:
                company_name = elem.get_text(strip=True)
            
            if not company_name or len(company_name) < 2 or len(company_name) > 100:
                return None
            
            # Skip if already seen
            name_key = company_name.lower().strip()
            if name_key in seen_names:
                return None
            
            # Extract domain
            domain = None
            
            # Look for website link
            website_link = elem.find('a', href=re.compile(r'^https?://'))
            if website_link:
                href = website_link.get('href', '')
                parsed = urlparse(href)
                domain = parsed.netloc.replace('www.', '')
                
                # Check if domain should be excluded
                if any(exclude in domain.lower() for exclude in config.exclude_domains):
                    domain = None
            
            # Look in parent element
            if not domain:
                parent = elem.find_parent(['div', 'article', 'section'])
                if parent:
                    parent_links = parent.find_all('a', href=re.compile(r'^https?://'))
                    for link in parent_links:
                        href = link.get('href', '')
                        parsed = urlparse(href)
                        potential_domain = parsed.netloc.replace('www.', '')
                        if not any(exclude in potential_domain.lower() for exclude in config.exclude_domains):
                            domain = potential_domain
                            break
            
            # Discover domain from name if needed
            if not domain:
                domain = await self._discover_domain_from_name(company_name)
            
            # Extract additional data
            focus_areas = []
            batch = ''
            year = None
            
            # Look for focus areas/industry
            text_content = elem.get_text() if hasattr(elem, 'get_text') else str(elem)
            if 'B2B' in text_content or 'b2b' in text_content.lower():
                focus_areas.append('B2B SaaS')
            if 'AI' in text_content or 'artificial intelligence' in text_content.lower():
                focus_areas.append('AI/ML')
            if 'Fintech' in text_content or 'fintech' in text_content.lower():
                focus_areas.append('Fintech')
            
            # Look for batch/year
            batch_match = re.search(r'([WS]\d{2})', text_content)
            if batch_match:
                batch = batch_match.group(1)
            
            year_match = re.search(r'(20\d{2})', text_content)
            if year_match:
                year = year_match.group(1)
            
            return {
                'name': company_name.strip(),
                'domain': domain or '',
                'source': config.name.lower().replace(' ', '_'),
                'focus_areas': focus_areas,
                'yc_batch': batch,
                'year': year,
                'portfolio_url': config.url
            }
            
        except Exception as e:
            return None
    
    async def _generic_extraction(
        self, 
        soup: BeautifulSoup, 
        config: PortfolioConfig, 
        seen_domains: Set[str], 
        seen_names: Set[str]
    ) -> List[Dict]:
        """Generic extraction fallback"""
        companies = []
        
        # Look for company links
        company_links = soup.find_all('a', href=re.compile(r'/companies/|/company/|/portfolio/'))
        for link in company_links[:1000]:  # Limit to avoid duplicates
            company = await self._extract_company_from_element(link, config, seen_domains, seen_names)
            if company:
                companies.append(company)
        
        # Look for company cards
        company_cards = soup.find_all(['div', 'article'], class_=re.compile(r'company|portfolio|card', re.I))
        for card in company_cards[:500]:
            company = await self._extract_company_from_element(card, config, seen_domains, seen_names)
            if company:
                companies.append(company)
        
        return companies
    
    async def _discover_domain_from_name(self, company_name: str) -> Optional[str]:
        """Try to discover domain from company name"""
        if not company_name or len(company_name) < 2:
            return None
        
        # Clean company name
        clean_name = re.sub(r'[^\w\s-]', '', company_name.lower().strip())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Generate potential domains
        no_spaces = clean_name.replace(' ', '').replace('-', '')
        
        # Return most likely domain (will be validated later)
        return f"{no_spaces}.com" if no_spaces else None
    
    def _validate_companies(self, companies: List[Dict], config: PortfolioConfig) -> List[Dict]:
        """Validate and clean company data for enterprise-grade quality"""
        validated = []
        seen_domains = set()
        seen_names = set()
        
        for company in companies:
            # Basic validation
            name = company.get('name', '').strip()
            domain = company.get('domain', '').lower().strip()
            
            # Skip if no name
            if not name or len(name) < 2:
                continue
            
            # Skip if name is too long (likely not a company name)
            if len(name) > 100:
                continue
            
            # Skip common non-company text
            skip_terms = [
                'load more', 'load', 'more', 'view', 'see', 'learn', 'read',
                'filter', 'search', 'sort', 'apply', 'contact', 'about', 'blog',
                'careers', 'jobs', 'privacy', 'terms', 'cookie'
            ]
            if any(term in name.lower() for term in skip_terms):
                continue
            
            # Skip if it's just a number
            if name.strip().isdigit():
                continue
            
            # Deduplicate by domain
            if domain:
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
            
            # Deduplicate by name
            name_key = name.lower().strip()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)
            
            # Ensure domain format is valid
            if domain:
                # Basic domain validation
                if '.' not in domain or len(domain.split('.')) < 2:
                    domain = None
                elif len(domain) < 4:  # Too short to be valid
                    domain = None
            
            # Clean and standardize
            validated_company = {
                'name': name,
                'domain': domain or '',
                'source': company.get('source', config.name.lower().replace(' ', '_')),
                'focus_areas': company.get('focus_areas', []),
                'yc_batch': company.get('yc_batch', ''),
                'year': company.get('year'),
                'portfolio_url': config.url
            }
            
            validated.append(validated_company)
        
        print(f"[PORTFOLIO-SCRAPER] Validated {len(validated)} companies from {len(companies)} raw companies")
        return validated
    
    # Convenience methods for known portfolios
    async def scrape_yc_portfolio(self, max_companies: int = 10000) -> List[Dict]:
        """Scrape Y Combinator portfolio"""
        config = PortfolioConfig(
            name="Y Combinator",
            url="https://www.ycombinator.com/companies",
            scroll_type="infinite",
            company_selectors=[
                'a[href*="/companies/"]',
                '[class*="Company"]',
                '[class*="company"]'
            ],
            exclude_domains=['ycombinator.com', 'twitter.com', 'linkedin.com'],
            max_companies=max_companies,
            scroll_wait_time=2.0,
            max_scroll_attempts=500,
            max_no_change_count=5
        )
        return await self.scrape_portfolio(config)
    
    async def scrape_antler_portfolio(self, max_companies: int = 5000) -> List[Dict]:
        """Scrape Antler portfolio"""
        config = PortfolioConfig(
            name="Antler",
            url="https://www.antler.co/portfolio",
            scroll_type="load_more",
            company_selectors=[
                '[class*="company"]',
                '[class*="portfolio"]',
                '[class*="card"]'
            ],
            load_more_selectors=[
                'button:has-text("Load More")',
                'button:has-text("Load more")',
                'a:has-text("Load More")',
                '[class*="load-more"]',
                '[class*="loadMore"]'
            ],
            exclude_domains=['antler.co', 'antler.com'],
            max_companies=max_companies,
            load_more_wait_time=2.0,
            max_scroll_attempts=200
        )
        return await self.scrape_portfolio(config)
    
    async def scrape_both_portfolios(self) -> Dict[str, List[Dict]]:
        """Scrape both YC and Antler portfolios concurrently"""
        print("[PORTFOLIO-SCRAPER] Starting scrape of both YC and Antler portfolios...")
        
        yc_task = self.scrape_yc_portfolio()
        antler_task = self.scrape_antler_portfolio()
        
        yc_companies, antler_companies = await asyncio.gather(
            yc_task,
            antler_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(yc_companies, Exception):
            print(f"[PORTFOLIO-SCRAPER] YC scrape failed: {yc_companies}")
            yc_companies = []
        
        if isinstance(antler_companies, Exception):
            print(f"[PORTFOLIO-SCRAPER] Antler scrape failed: {antler_companies}")
            antler_companies = []
        
        return {
            'yc': yc_companies if isinstance(yc_companies, list) else [],
            'antler': antler_companies if isinstance(antler_companies, list) else []
        }
