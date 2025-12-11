"""
Observable Portfolio Scraper with Screenshot Capture and Progress Tracking
Provides full visibility into scraping operations
"""
import asyncio
import json
import base64
from typing import List, Dict, Optional, Set, Callable, Any
import re
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from bs4 import BeautifulSoup

# Progress callback type
ProgressCallback = Callable[[Dict[str, Any]], None]


class ObservablePortfolioScraper:
    """Portfolio scraper with full observability - screenshots, progress tracking, and browser monitoring"""
    
    def __init__(self, progress_callback: Optional[ProgressCallback] = None):
        self.playwright = None
        self.browser = None
        self.page = None
        self.progress_callback = progress_callback
        self.screenshots_dir = Path("artifacts/portfolio_scraping")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def _emit_progress(self, event_type: str, data: Dict[str, Any]):
        """Emit progress event to callback"""
        if self.progress_callback:
            try:
                self.progress_callback({
                    'type': event_type,
                    'timestamp': datetime.now().isoformat(),
                    **data
                })
            except Exception as e:
                print(f"[OBSERVABLE] Error emitting progress: {e}")
    
    async def _take_screenshot(self, page, label: str, portfolio_name: str) -> Optional[str]:
        """Take screenshot and return base64 encoded data"""
        try:
            screenshot_bytes = await page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Save screenshot to disk
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{portfolio_name}_{label}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            filepath.write_bytes(screenshot_bytes)
            
            await self._emit_progress('screenshot', {
                'label': label,
                'portfolio': portfolio_name,
                'filename': filename,
                'screenshot': screenshot_b64,
                'url': await page.url if page else None
            })
            
            return screenshot_b64
        except Exception as e:
            print(f"[OBSERVABLE] Error taking screenshot: {e}")
            return None
    
    async def scrape_yc_portfolio_observable(
        self, 
        max_companies: int = 10000,
        screenshot_interval: int = 10  # Take screenshot every N scrolls
    ) -> List[Dict]:
        """Scrape YC portfolio with full observability - ensures browser cleanup"""
        companies = []
        seen_domains = set()
        seen_names = set()
        portfolio_name = "YC"
        
        url = "https://www.ycombinator.com/companies"
        
        await self._emit_progress('start', {
            'portfolio': portfolio_name,
            'url': url,
            'max_companies': max_companies
        })
        
        if not PLAYWRIGHT_AVAILABLE:
            await self._emit_progress('error', {
                'portfolio': portfolio_name,
                'message': 'Playwright not available'
            })
            return []
        
        browser = None
        page = None
        playwright = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            
            # Set a timeout for page operations
            page.set_default_timeout(30000)
            
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            await self._emit_progress('navigate', {
                'portfolio': portfolio_name,
                'url': url
            })
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)
            
            # Initial screenshot
            await self._take_screenshot(page, "initial_load", portfolio_name)
            
            previous_count = 0
            no_change_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 500
            
            await self._emit_progress('scrolling_start', {
                'portfolio': portfolio_name
            })
            
            while scroll_attempts < max_scroll_attempts and len(companies) < max_companies:
                # Extract companies
                page_companies = await self._extract_yc_companies_from_page(page, seen_domains, seen_names)
                
                for company in page_companies:
                    domain = company.get('domain', '').lower().strip()
                    name = company.get('name', '').lower().strip()
                    
                    if domain:
                        seen_domains.add(domain)
                    if name:
                        seen_names.add(name)
                    
                    companies.append(company)
                
                current_count = len(companies)
                
                # Progress update with batch of new companies
                new_companies_batch = companies[previous_count:] if previous_count < len(companies) else []
                await self._emit_progress('progress', {
                    'portfolio': portfolio_name,
                    'companies_found': current_count,
                    'scroll_attempt': scroll_attempts,
                    'companies_on_page': len(page_companies),
                    'new_companies': current_count - previous_count,
                    'companies_batch': new_companies_batch[:10]  # Emit up to 10 companies per batch
                })
                
                # Screenshot every N scrolls
                if scroll_attempts % screenshot_interval == 0:
                    await self._take_screenshot(page, f"scroll_{scroll_attempts}", portfolio_name)
                
                # Check if still finding new companies
                if current_count == previous_count:
                    no_change_count += 1
                    if no_change_count >= 5:
                        await self._emit_progress('scrolling_stop', {
                            'portfolio': portfolio_name,
                            'reason': 'no_new_companies',
                            'companies_found': current_count
                        })
                        break
                else:
                    no_change_count = 0
                
                previous_count = current_count
                
                # Scroll
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                scroll_attempts += 1
            
            await self._take_screenshot(page, "final", portfolio_name)
        except Exception as e:
            await self._emit_progress('error', {
                'portfolio': portfolio_name,
                'error': str(e)
            })
            import traceback
            traceback.print_exc()
        finally:
            # ALWAYS close browser resources, even on exception
            # Close in reverse order: page -> browser -> playwright
            if page:
                try:
                    await page.close()
                    page = None
                except Exception as e:
                    print(f"[OBSERVABLE] Error closing page: {e}")
            if browser:
                try:
                    await browser.close()
                    browser = None
                except Exception as e:
                    print(f"[OBSERVABLE] Error closing browser: {e}")
            if playwright:
                try:
                    await playwright.stop()
                    playwright = None
                except Exception as e:
                    print(f"[OBSERVABLE] Error stopping playwright: {e}")
            # Small delay to ensure cleanup completes
            await asyncio.sleep(0.2)
        
        await self._emit_progress('complete', {
            'portfolio': portfolio_name,
            'companies_found': len(companies)
        })
        
        return companies
    
    async def scrape_antler_portfolio_observable(
        self,
        max_companies: int = 5000,
        screenshot_interval: int = 5  # Take screenshot every N clicks
    ) -> List[Dict]:
        """Scrape Antler portfolio with full observability"""
        companies = []
        seen_domains = set()
        seen_names = set()
        portfolio_name = "Antler"
        
        url = "https://www.antler.co/portfolio"
        
        await self._emit_progress('start', {
            'portfolio': portfolio_name,
            'url': url,
            'max_companies': max_companies
        })
        
        if not PLAYWRIGHT_AVAILABLE:
            await self._emit_progress('error', {
                'portfolio': portfolio_name,
                'message': 'Playwright not available'
            })
            return []
        
        browser = None
        page = None
        playwright = None
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']  # Additional args for stability
            )
            page = await browser.new_page()
            
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            await self._emit_progress('navigate', {
                'portfolio': portfolio_name,
                'url': url
            })
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
            
            # Initial screenshot
            await self._take_screenshot(page, "initial_load", portfolio_name)
            
            load_more_attempts = 0
            max_load_more_attempts = 200
            
            await self._emit_progress('load_more_start', {
                'portfolio': portfolio_name
            })
            
            while load_more_attempts < max_load_more_attempts and len(companies) < max_companies:
                # Extract companies
                page_companies = await self._extract_antler_companies_from_page(page, seen_domains, seen_names)
                
                for company in page_companies:
                    domain = company.get('domain', '').lower().strip()
                    name = company.get('name', '').lower().strip()
                    
                    if domain:
                        seen_domains.add(domain)
                    if name:
                        seen_names.add(name)
                    
                    companies.append(company)
                
                current_count = len(companies)
                
                # Progress update with batch of new companies
                previous_batch_count = len(companies) - len(page_companies)
                new_companies_batch = companies[previous_batch_count:] if previous_batch_count >= 0 else page_companies
                await self._emit_progress('progress', {
                    'portfolio': portfolio_name,
                    'companies_found': current_count,
                    'load_more_attempt': load_more_attempts,
                    'companies_on_page': len(page_companies),
                    'companies_batch': new_companies_batch[:10]  # Emit up to 10 companies per batch
                })
                
                # Screenshot every N clicks
                if load_more_attempts % screenshot_interval == 0:
                    await self._take_screenshot(page, f"load_more_{load_more_attempts}", portfolio_name)
                
                # Try to click Load More
                load_more_clicked = False
                load_more_selectors = [
                    'button:has-text("Load More")',
                    'button:has-text("Load more")',
                    'a:has-text("Load More")',
                    '[class*="load-more"]'
                ]
                
                for selector in load_more_selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button and await button.is_visible():
                            await self._emit_progress('button_click', {
                                'portfolio': portfolio_name,
                                'selector': selector,
                                'attempt': load_more_attempts
                            })
                            await button.click()
                            await asyncio.sleep(2)
                            load_more_clicked = True
                            break
                    except:
                        continue
                
                if not load_more_clicked:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                    
                    # Check again after scroll
                    for selector in load_more_selectors:
                        try:
                            button = await page.query_selector(selector)
                            if button and await button.is_visible():
                                await button.click()
                                await asyncio.sleep(2)
                                load_more_clicked = True
                                break
                        except:
                            continue
                
                if not load_more_clicked and len(page_companies) == 0:
                    await self._emit_progress('load_more_stop', {
                        'portfolio': portfolio_name,
                        'reason': 'no_button_found',
                        'companies_found': current_count
                    })
                    break
                
                load_more_attempts += 1
            
            await self._take_screenshot(page, "final", portfolio_name)
        except Exception as e:
            await self._emit_progress('error', {
                'portfolio': portfolio_name,
                'error': str(e)
            })
            import traceback
            traceback.print_exc()
        finally:
            # ALWAYS close browser resources, even on exception
            # Close in reverse order: page -> browser -> playwright
            if page:
                try:
                    await page.close()
                    page = None
                except Exception as e:
                    print(f"[OBSERVABLE] Error closing page: {e}")
            if browser:
                try:
                    await browser.close()
                    browser = None
                except Exception as e:
                    print(f"[OBSERVABLE] Error closing browser: {e}")
            if playwright:
                try:
                    await playwright.stop()
                    playwright = None
                except Exception as e:
                    print(f"[OBSERVABLE] Error stopping playwright: {e}")
            # Small delay to ensure cleanup completes
            await asyncio.sleep(0.2)
        
        await self._emit_progress('complete', {
            'portfolio': portfolio_name,
            'companies_found': len(companies)
        })
        
        return companies
    
    async def _extract_yc_companies_from_page(self, page, seen_domains: Set[str], seen_names: Set[str]) -> List[Dict]:
        """Extract companies from YC page using JavaScript to handle React-rendered content"""
        companies = []
        try:
            # Use JavaScript to extract companies since YC page is React-rendered
            extracted = await page.evaluate('''() => {
                const companies = [];
                const links = Array.from(document.querySelectorAll("a[href*='/companies/']"));
                const seen = new Set();
                
                for (let link of links) {
                    const href = link.getAttribute('href') || link.href;
                    const match = href.match(/\\/companies\\/([^/]+)/);
                    if (!match) continue;
                    
                    const slug = match[1];
                    if (seen.has(slug)) continue;
                    seen.add(slug);
                    
                    // Extract company name - try to get just the first word/text node
                    let company_name = slug.replace(/-/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                    
                    // Try to find a better name from the link text
                    const linkText = link.textContent.trim();
                    // Company name is usually the first part before location/description
                    const nameMatch = linkText.match(/^([A-Z][a-zA-Z0-9\\s&]+?)(?:[A-Z]{2,}|San Francisco|Bengaluru|Palo Alto|Berkeley|New York|London|Tel Aviv)/);
                    if (nameMatch && nameMatch[1].length > 2 && nameMatch[1].length < 50) {
                        company_name = nameMatch[1].trim();
                    } else {
                        // Fallback: take first reasonable word sequence
                        const words = linkText.split(/[A-Z]{2,}|San Francisco|Bengaluru/)[0].trim();
                        if (words.length > 2 && words.length < 50) {
                            company_name = words;
                        }
                    }
                    
                    // Try to find domain from the card/parent element
                    let domain = null;
                    const card = link.closest('div, article, li, section');
                    if (card) {
                        const websiteLink = card.querySelector('a[href^="http"]:not([href*="ycombinator"]):not([href*="twitter"]):not([href*="linkedin"]):not([href*="facebook"]):not([href*="startupschool"])');
                        if (websiteLink) {
                            try {
                                const url = new URL(websiteLink.href);
                                domain = url.hostname.replace('www.', '');
                            } catch(e) {}
                        }
                    }
                    
                    companies.push({
                        name: company_name,
                        slug: slug,
                        domain: domain,
                        url: href.startsWith('http') ? href : `https://www.ycombinator.com${href}`
                    });
                }
                return companies;
            }''')
            
            # Process extracted companies
            for item in extracted:
                try:
                    company_name = item.get('name', '').strip()
                    slug = item.get('slug', '')
                    domain = item.get('domain')
                    company_url = item.get('url', '')
                    
                    if not company_name or len(company_name) < 2:
                        continue
                    
                    name_key = company_name.lower().strip()
                    if name_key in seen_names:
                        continue
                    
                    # If no domain found, try to get it from the company detail page
                    if not domain and company_url:
                        try:
                            # Navigate to company page to get domain
                            detail_page = await page.context.new_page()
                            await detail_page.goto(company_url, wait_until='networkidle', timeout=15000)
                            await asyncio.sleep(1)  # Brief wait for React
                            
                            domain_result = await detail_page.evaluate('''() => {
                                const websiteLink = document.querySelector('a[href^="http"]:not([href*="ycombinator"]):not([href*="twitter"]):not([href*="linkedin"]):not([href*="facebook"]):not([href*="startupschool"])');
                                if (websiteLink) {
                                    try {
                                        const url = new URL(websiteLink.href);
                                        return url.hostname.replace('www.', '');
                                    } catch(e) {}
                                }
                                return null;
                            }''')
                            
                            if domain_result:
                                domain = domain_result
                            
                            await detail_page.close()
                        except Exception as e:
                            print(f"[OBSERVABLE] Error fetching domain for {company_name}: {e}")
                    
                    # If still no domain, derive from slug (better than generating fake domain)
                    if not domain:
                        # Try common domain patterns
                        domain_candidates = [
                            f"{slug}.com",
                            f"{slug}.io",
                            f"{slug}.ai",
                            f"{slug}.co"
                        ]
                        # Don't auto-generate, leave empty - we'll skip companies without domains
                        domain = None
                    
                    # Only add if we have a domain or if it's a well-known company
                    if domain:
                        companies.append({
                            'name': company_name,
                            'domain': domain,
                            'source': 'yc',
                            'yc_batch': '',  # Could extract from page if needed
                            'focus_areas': [],
                            'portfolio_url': 'https://www.ycombinator.com/companies'
                        })
                        
                        seen_names.add(name_key)
                        seen_domains.add(domain.lower())
                except Exception as e:
                    print(f"[OBSERVABLE] Error processing company {item.get('name', 'unknown')}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[OBSERVABLE] Error extracting YC companies: {e}")
            import traceback
            traceback.print_exc()
        
        return companies
    
    async def _extract_antler_companies_from_page(self, page, seen_domains: Set[str], seen_names: Set[str]) -> List[Dict]:
        """Extract companies from Antler page"""
        companies = []
        try:
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            company_cards = soup.find_all(['div', 'article', 'a'], class_=re.compile(r'company|portfolio|card', re.I))
            
            for card in company_cards:
                try:
                    name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div'], class_=re.compile(r'name|title', re.I))
                    if not name_elem:
                        name_elem = card.find(string=re.compile(r'^[A-Z][a-zA-Z0-9\s&]+$'))
                    
                    if name_elem:
                        company_name = name_elem.get_text(strip=True) if hasattr(name_elem, 'get_text') else str(name_elem).strip()
                        
                        if not company_name or len(company_name) < 2 or len(company_name) > 80:
                            continue
                        
                        skip_terms = ['load more', 'load', 'more', 'antler', 'portfolio', 'apply']
                        if any(term in company_name.lower() for term in skip_terms):
                            continue
                        
                        name_key = company_name.lower().strip()
                        if name_key in seen_names:
                            continue
                        
                        domain = None
                        website_link = card.find('a', href=re.compile(r'^https?://'))
                        if website_link:
                            href = website_link.get('href', '')
                            if href and 'antler.co' not in href.lower():
                                parsed = urlparse(href)
                                domain = parsed.netloc.replace('www.', '')
                        
                        if not domain:
                            domain = await self._discover_domain_from_name(company_name)
                        
                        companies.append({
                            'name': company_name.strip(),
                            'domain': domain or '',
                            'source': 'antler',
                            'focus_areas': [],
                            'portfolio_url': 'https://www.antler.co/portfolio'
                        })
                        
                        seen_names.add(name_key)
                        if domain:
                            seen_domains.add(domain.lower())
                except:
                    continue
        except Exception as e:
            print(f"[OBSERVABLE] Error extracting Antler companies: {e}")
        
        return companies
    
    async def _discover_domain_from_name(self, company_name: str) -> Optional[str]:
        """Discover domain from company name"""
        if not company_name or len(company_name) < 2:
            return None
        
        clean_name = re.sub(r'[^\w\s-]', '', company_name.lower().strip())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        no_spaces = clean_name.replace(' ', '').replace('-', '')
        
        return f"{no_spaces}.com" if no_spaces else None
    
    async def scrape_both_observable(self) -> Dict[str, List[Dict]]:
        """Scrape both portfolios with observability - ensures proper browser cleanup"""
        await self._emit_progress('start_both', {
            'portfolios': ['YC', 'Antler']
        })
        
        yc_companies = []
        antler_companies = []
        
        # Run scrapers sequentially to avoid browser leaks and ensure proper cleanup
        # Each scraper manages its own playwright instance and browser
        try:
            yc_companies = await self.scrape_yc_portfolio_observable()
        except Exception as e:
            print(f"[OBSERVABLE] Error scraping YC portfolio: {e}")
            import traceback
            traceback.print_exc()
            await self._emit_progress('error', {
                'portfolio': 'YC',
                'error': str(e)
            })
            yc_companies = []
        
        # Ensure YC browser is closed before starting Antler
        await asyncio.sleep(0.5)  # Small delay to ensure cleanup completes
        
        try:
            antler_companies = await self.scrape_antler_portfolio_observable()
        except Exception as e:
            print(f"[OBSERVABLE] Error scraping Antler portfolio: {e}")
            import traceback
            traceback.print_exc()
            await self._emit_progress('error', {
                'portfolio': 'Antler',
                'error': str(e)
            })
            antler_companies = []
        
        await self._emit_progress('complete_both', {
            'yc_count': len(yc_companies),
            'antler_count': len(antler_companies)
        })
        
        return {
            'yc': yc_companies,
            'antler': antler_companies
        }




