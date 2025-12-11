"""
Browser-based scraper using Playwright for JavaScript-heavy sites
Based on patterns from Skyvern, Noyori, and Gonzales repos
"""
import asyncio
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import aiohttp

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available. Install with: pip install playwright && playwright install chromium")

class BrowserScraper:
    """
    Playwright-based browser scraper for JavaScript-heavy sites.
    Extracts companies and technical details for optimization.
    """
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        if PLAYWRIGHT_AVAILABLE:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_with_browser(
        self, 
        url: str, 
        wait_selectors: Optional[List[str]] = None,
        wait_timeout: int = 30000,
        extract_technical_details: bool = True
    ) -> Dict:
        """
        Scrape a URL using Playwright browser automation.
        
        Args:
            url: URL to scrape
            wait_selectors: List of CSS selectors to wait for (ensures content loaded)
            wait_timeout: Timeout in milliseconds
            extract_technical_details: Whether to extract technical details for optimization
            
        Returns:
            Dict with 'html', 'companies', 'technical_details'
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {
                'html': None,
                'companies': [],
                'technical_details': {},
                'error': 'Playwright not available'
            }
        
        if not self.context:
            return {
                'html': None,
                'companies': [],
                'technical_details': {},
                'error': 'Browser context not initialized'
            }
        
        page = await self.context.new_page()
        companies = []
        technical_details = {}
        
        try:
            # Navigate to URL
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until='domcontentloaded', timeout=wait_timeout)
            
            # Wait for specific selectors if provided
            if wait_selectors:
                for selector in wait_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000, state='visible')
                        print(f"Found selector: {selector}")
                    except Exception as e:
                        print(f"Selector {selector} not found: {e}")
            
            # Wait for network to be idle (ensures JavaScript has loaded)
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except:
                # If networkidle times out, continue anyway
                pass
            
            # Extract technical details for optimization
            if extract_technical_details:
                technical_details = await self._extract_technical_details(page, url)
            
            # Get page HTML
            html = await page.content()
            
            # Extract companies from the page
            companies = await self._extract_companies_from_page(page, url)
            
            return {
                'html': html,
                'companies': companies,
                'technical_details': technical_details,
                'url': url,
                'success': True
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {
                'html': None,
                'companies': [],
                'technical_details': {},
                'error': str(e),
                'success': False
            }
        finally:
            await page.close()
    
    async def _extract_technical_details(self, page: Page, url: str) -> Dict:
        """
        Extract technical details about the page structure for optimization.
        This helps identify patterns for future scraping.
        """
        details = {
            'framework': None,
            'data_attributes': [],
            'api_endpoints': [],
            'selectors': {},
            'rendering_method': 'unknown'
        }
        
        try:
            # Check for common frameworks
            framework_checks = await page.evaluate("""
                () => {
                    const checks = {};
                    checks.react = !!window.React || !!document.querySelector('[data-reactroot]');
                    checks.vue = !!window.Vue || !!document.querySelector('[data-v-]');
                    checks.angular = !!window.angular || !!document.querySelector('[ng-app]');
                    checks.nextjs = !!window.__NEXT_DATA__;
                    return checks;
                }
            """)
            
            for framework, detected in framework_checks.items():
                if detected:
                    details['framework'] = framework
                    break
            
            # Extract data attributes that might contain company data
            data_attrs = await page.evaluate("""
                () => {
                    const attrs = new Set();
                    document.querySelectorAll('[data-company], [data-name], [data-url], [data-website]').forEach(el => {
                        Object.keys(el.dataset).forEach(key => attrs.add(key));
                    });
                    return Array.from(attrs);
                }
            """)
            details['data_attributes'] = data_attrs
            
            # Look for API endpoints in network requests or script tags
            # This helps identify if there's a better API to use
            api_endpoints = await page.evaluate("""
                () => {
                    const endpoints = [];
                    // Check for common API patterns in script tags
                    document.querySelectorAll('script').forEach(script => {
                        const content = script.textContent || '';
                        const matches = content.match(/https?:\\/\\/[^"'\\s]+\\/(api|graphql|v1|v2)[^"'\\s]*/g);
                        if (matches) {
                            endpoints.push(...matches.slice(0, 5)); // Limit to 5
                        }
                    });
                    return [...new Set(endpoints)];
                }
            """)
            details['api_endpoints'] = api_endpoints[:10]  # Limit to 10
            
            # Identify key selectors for company data
            selectors = await page.evaluate("""
                () => {
                    const selectors = {};
                    // Look for common patterns
                    const companyLinks = document.querySelectorAll('a[href*="/companies/"], a[href*="/company/"]');
                    if (companyLinks.length > 0) {
                        selectors.company_links = 'a[href*="/companies/"], a[href*="/company/"]';
                    }
                    
                    const companyCards = document.querySelectorAll('[class*="company"], [class*="portfolio"], [class*="startup"]');
                    if (companyCards.length > 0) {
                        selectors.company_cards = '[class*="company"], [class*="portfolio"], [class*="startup"]';
                    }
                    
                    return selectors;
                }
            """)
            details['selectors'] = selectors
            
            # Determine rendering method
            if details['framework']:
                details['rendering_method'] = f"client-side ({details['framework']})"
            else:
                details['rendering_method'] = "server-side"
                
        except Exception as e:
            print(f"Error extracting technical details: {e}")
        
        return details
    
    async def _extract_companies_from_page(self, page: Page, url: str) -> List[Dict]:
        """
        Extract company information from the page.
        Uses multiple strategies to find company data.
        """
        companies = []
        seen_companies = set()
        
        try:
            # Strategy 1: Extract from links
            company_links = await page.query_selector_all('a[href*="/companies/"], a[href*="/company/"]')
            for link in company_links[:200]:  # Limit to 200
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    
                    if not text or len(text.strip()) < 2:
                        continue
                    
                    # Clean company name - YC format often concatenates name and location
                    # Pattern: "CompanyNameLocation" or "CompanyName Location, State"
                    lines = text.strip().split('\n')
                    company_name = lines[0].strip()
                    
                    # Detect where company name ends and location begins
                    # Common pattern: Company name ends before a city name (capitalized word)
                    # Try splitting on city names
                    city_keywords = ['San Francisco', 'New York', 'Palo Alto', 'Mountain View', 
                                   'Santa Clara', 'Boston', 'Seattle', 'Austin', 'London', 'Toronto',
                                   'Los Angeles', 'Chicago', 'Denver', 'Portland', 'Cambridge']
                    
                    # Find the earliest city keyword occurrence
                    earliest_city_pos = len(company_name)
                    for city in city_keywords:
                        pos = company_name.find(city)
                        if pos != -1 and pos < earliest_city_pos:
                            earliest_city_pos = pos
                    
                    if earliest_city_pos < len(company_name):
                        company_name = company_name[:earliest_city_pos].strip()
                    
                    # Remove location patterns with commas and states
                    company_name = re.sub(r',\s*[A-Z]{2},?\s*USA.*', '', company_name)  # "City, STATE, USA"
                    company_name = re.sub(r',\s*[A-Z][a-z]+,?\s*USA.*', '', company_name)  # "City, State, USA"
                    company_name = re.sub(r',\s*[A-Z][a-z]+.*', '', company_name)  # "City, Country"
                    
                    # Remove common suffixes/prefixes
                    company_name = re.sub(r'\s*\(.*?\)\s*$', '', company_name)
                    company_name = re.sub(r'\s*\[.*?\]\s*$', '', company_name)
                    company_name = company_name.strip()
                    
                    # Handle concatenated names (e.g., "GrowwBengaluru" -> "Groww", "MatterportSunnyvale" -> "Matterport")
                    # Detect camelCase or PascalCase transitions that might indicate location
                    city_keywords = ['Bengaluru', 'Berkeley', 'Menlo', 'Palo', 'Mountain', 'Santa', 'San', 'New', 'Los', 'Boston', 'Seattle', 'Austin', 'London', 'Toronto', 'Cambridge', 'Brooklyn', 'Sunnyvale', 'Lehi', 'Park']
                    
                    # Check for concatenated city names (no space before city)
                    for city in city_keywords:
                        # Try different case variations
                        patterns = [city, city.lower(), city.capitalize()]
                        for pattern in patterns:
                            if pattern in company_name:
                                # Find where city name starts
                                city_pos = company_name.find(pattern)
                                if city_pos > 2:  # Make sure we have a reasonable company name
                                    # Check character before city
                                    if city_pos > 0:
                                        before_char = company_name[city_pos - 1]
                                        # If before char is uppercase or lowercase (not space), it's concatenated
                                        if before_char.isalnum():
                                            company_name = company_name[:city_pos].strip()
                                            break
                                    # Also handle "City" or "Park" at the end
                                    if pattern in ['Park', 'City'] and company_name.endswith(pattern):
                                        # Find where it starts (usually after a city name)
                                        # For "Menlo Park", "Mountain View", etc.
                                        for city_start in ['Menlo', 'Mountain', 'Sunnyvale', 'Santa']:
                                            if city_start in company_name:
                                                start_pos = company_name.find(city_start)
                                                if start_pos > 2:
                                                    company_name = company_name[:start_pos].strip()
                                                    break
                                        break
                        # Break outer loop if we found and processed a city
                        if pattern in company_name and city_pos > 2:
                            break
                    
                    # Final cleanup: if still has issues, take first 1-3 words
                    if ',' in company_name or len(company_name) > 50:
                        words = company_name.split()
                        # Company names are usually 1-3 words
                        if len(words) > 3:
                            # Try to find where location starts
                            for i, word in enumerate(words):
                                if word.lower() in ['san', 'new', 'palo', 'mountain', 'santa', 'boston', 'seattle', 'austin', 'bengaluru', 'berkeley', 'menlo']:
                                    company_name = ' '.join(words[:i])
                                    break
                            else:
                                company_name = ' '.join(words[:3])  # Take first 3 words as fallback
                    
                    if len(company_name) < 2 or len(company_name) > 80:
                        continue
                    
                    # Skip filter UI elements and non-company text
                    skip_terms = ['filter', 'field', 'option', 'select', 'all', 'none', 'apply', 'clear', 'search', 'sort', 
                                 'email address', 'phone number', 'job', 'jobs', 'careers', 'about', 'contact', 'blog']
                    if any(term in company_name.lower() for term in skip_terms):
                        continue
                    
                    # Skip if looks like UI element (short, common words or numbers)
                    if len(company_name) <= 3 and company_name.lower() in ['all', 'any', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']:
                        continue
                    
                    # Skip if it's just a number
                    if company_name.strip().isdigit():
                        continue
                    
                    # Skip if it's a description (too long, contains "is", "are", "helping", etc.)
                    description_indicators = ['is helping', 'is building', 'is making', 'is revolutionizing', 'is simplifying']
                    if any(indicator in company_name.lower() for indicator in description_indicators):
                        continue
                    
                    # Skip if it looks like a headline (contains "The #", "Private,", etc.)
                    if 'The #' in company_name or (company_name.startswith('Private') and ',' in company_name):
                        continue
                    
                    name_key = company_name.lower().strip()
                    
                    if name_key in seen_companies:
                        continue
                    seen_companies.add(name_key)
                    
                    # Extract domain from href or nearby elements
                    domain = None
                    if href:
                        # Try to get full URL
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc and parsed.netloc not in ['ycombinator.com', 'www.ycombinator.com']:
                            domain = parsed.netloc.replace('www.', '')
                    
                    # Look for domain in parent element or sibling elements
                    if not domain:
                        try:
                            parent = await link.evaluate_handle('el => el.closest("div, article, li, section")')
                            if parent:
                                # Look for external links in parent
                                parent_links = await parent.query_selector_all('a[href^="http"]')
                                for plink in parent_links[:5]:
                                    plink_href = await plink.get_attribute('href')
                                    if plink_href:
                                        parsed = urlparse(plink_href)
                                        if parsed.netloc and 'ycombinator' not in parsed.netloc.lower():
                                            domain = parsed.netloc.replace('www.', '').lower()
                                            break
                                
                                # If still no domain, try text extraction
                                if not domain:
                                    parent_text = await parent.inner_text()
                                    domain_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9-]*\.(?:com|io|ai|co|dev|app|tech|org))', parent_text)
                                    if domain_match:
                                        potential_domain = domain_match.group(1).lower()
                                        if 'ycombinator' not in potential_domain:
                                            domain = potential_domain
                        except Exception as e:
                            pass
                    
                    # Try to extract from company page URL pattern (YC: /companies/company-name)
                    if not domain and href and '/companies/' in href:
                        # Extract company slug and try common domain patterns
                        company_slug = href.split('/companies/')[-1].split('/')[0].split('?')[0]
                        if company_slug:
                            # Try common domain patterns
                            potential_domains = [
                                f"{company_slug}.com",
                                f"{company_slug}.io",
                                f"{company_slug}.ai",
                                f"{company_slug.replace('-', '')}.com"
                            ]
                            # Note: We can't validate these without making requests, so we'll leave domain empty
                            # The domain discovery function will handle this later
                    
                    companies.append({
                        'name': company_name,
                        'domain': domain or '',
                        'source': 'browser_scraper',
                        'portfolio_url': url
                    })
                except Exception as e:
                    continue
            
            # Strategy 2: Extract from data attributes
            data_elements = await page.query_selector_all('[data-company], [data-name], [data-url]')
            for elem in data_elements[:100]:
                try:
                    company_name = await elem.get_attribute('data-company') or await elem.get_attribute('data-name')
                    domain = await elem.get_attribute('data-url') or await elem.get_attribute('data-website')
                    
                    if not company_name:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 2:
                            company_name = text.strip()
                    
                    if not company_name or len(company_name) < 2:
                        continue
                    
                    name_key = company_name.lower()
                    if name_key in seen_companies:
                        continue
                    seen_companies.add(name_key)
                    
                    if domain:
                        parsed = urlparse(domain)
                        domain = parsed.netloc.replace('www.', '') if parsed.netloc else domain
                    
                    # Use domain discovery if domain not found
                    if not domain:
                        try:
                            from portfolio_scraper import PortfolioScraper
                            temp_scraper = PortfolioScraper()
                            domain = await temp_scraper._discover_domain_from_name(company_name)
                        except:
                            pass
                    
                    companies.append({
                        'name': company_name,
                        'domain': domain or '',
                        'source': 'browser_scraper',
                        'portfolio_url': url
                    })
                except Exception as e:
                    continue
            
            # Strategy 3: Extract from visible text patterns (for specific sites)
            # For Antler: Look for actual company cards, not filter elements
            if 'antler.co' in url:
                # Antler has company cards with specific structure
                # Look for links that go to external company websites
                external_links = await page.query_selector_all('a[href^="http"]:not([href*="antler.co"])')
                for link in external_links[:100]:
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        if not text or len(text.strip()) < 2:
                            continue
                        
                        # Skip if it's a filter or UI element
                        skip_terms = ['filter', 'field', 'option', 'select', 'all', 'email', 'phone', 'job', 'career']
                        if any(term in text.lower() for term in skip_terms):
                            continue
                        
                        # Extract domain from href
                        parsed = urlparse(href)
                        domain = parsed.netloc.replace('www.', '') if parsed.netloc else None
                        
                        if not domain:
                            continue
                        
                        # Company name might be in link text or nearby
                        company_name = text.strip().split('\n')[0].strip()
                        
                        # If name is too generic, try to get it from parent
                        if len(company_name) < 3 or company_name.lower() in ['visit', 'website', 'learn more', 'read more']:
                            parent = await link.evaluate_handle('el => el.closest("div, article, section")')
                            if parent:
                                parent_text = await parent.inner_text()
                                # Try to extract company name from parent (usually first line)
                                lines = [l.strip() for l in parent_text.split('\n') if l.strip()]
                                if lines:
                                    company_name = lines[0]
                        
                        if len(company_name) < 2 or len(company_name) > 80:
                            continue
                        
                        name_key = company_name.lower().strip()
                        if name_key in seen_companies:
                            continue
                        seen_companies.add(name_key)
                        
                        companies.append({
                            'name': company_name,
                            'domain': domain,
                            'source': 'browser_scraper',
                            'portfolio_url': url
                        })
                    except Exception as e:
                        continue
            
            # Strategy 4: Extract from visible text patterns (for YC specifically)
            if 'ycombinator.com' in url:
                # YC has company names in specific structures
                company_elements = await page.query_selector_all('h3, h4, .company-name, [class*="Company"]')
                for elem in company_elements[:100]:
                    try:
                        text = await elem.inner_text()
                        if not text or len(text) < 2 or len(text) > 80:
                            continue
                        
                        # Skip common non-company text
                        skip_terms = ['y combinator', 'batch', 'apply', 'learn', 'read', 'view']
                        if any(term in text.lower() for term in skip_terms):
                            continue
                        
                        name_key = text.lower().strip()
                        if name_key in seen_companies:
                            continue
                        seen_companies.add(name_key)
                        
                        # Look for domain nearby
                        domain = None
                        parent = await elem.evaluate_handle('el => el.closest("div, article, li")')
                        if parent:
                            links = await parent.query_selector_all('a[href^="http"]')
                            for link in links[:5]:
                                href = await link.get_attribute('href')
                                if href:
                                    parsed = urlparse(href)
                                    if parsed.netloc and 'ycombinator' not in parsed.netloc:
                                        domain = parsed.netloc.replace('www.', '')
                                        break
                        
                        # Use domain discovery if domain not found
                        if not domain:
                            try:
                                from portfolio_scraper import PortfolioScraper
                                temp_scraper = PortfolioScraper()
                                domain = await temp_scraper._discover_domain_from_name(text.strip())
                            except:
                                pass
                        
                        companies.append({
                            'name': text.strip(),
                            'domain': domain or '',
                            'source': 'browser_scraper',
                            'portfolio_url': url
                        })
                    except Exception as e:
                        continue
            
        except Exception as e:
            print(f"Error extracting companies: {e}")
        
        return companies
    
    async def close(self):
        """Close browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

