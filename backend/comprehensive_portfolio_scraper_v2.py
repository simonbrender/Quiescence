"""
Comprehensive Portfolio Scraper V2 - High-Performance Scaling
Removes limits, adds pagination, improves extraction for ~6k+ companies
"""
import asyncio
import json
from typing import List, Dict, Optional, Set
import re
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False


class ComprehensivePortfolioScraper:
    """High-performance portfolio scraper designed to scale to 6k+ companies"""
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_yc_comprehensive(self) -> List[Dict]:
        """
        Comprehensive YC scraping - ALL batches, ALL companies
        Expected: ~4000+ companies across all batches
        """
        companies = []
        seen_companies = set()
        
        # ALL YC batches from inception to present
        # Format: W{year} or S{year} (Winter/Summer)
        all_batches = []
        for year in range(2005, 2025):  # YC started in 2005
            all_batches.extend([f'W{str(year)[-2:]}', f'S{str(year)[-2:]}'])
        
        print(f"[YC-COMPREHENSIVE] Scraping {len(all_batches)} YC batches...")
        
        # Use the existing YC batch scraper but with improved extraction
        try:
            from osint_sources import scrape_yc_batch
            
            for idx, batch in enumerate(all_batches):
                try:
                    print(f"[YC-COMPREHENSIVE] [{idx+1}/{len(all_batches)}] Scraping batch {batch}...")
                    batch_companies = await scrape_yc_batch(batch)
                    
                    # Deduplicate
                    for company in batch_companies:
                        domain = company.get('domain', '').lower().strip()
                        name = company.get('name', '').lower().strip()
                        key = domain or name
                        
                        if key and key not in seen_companies:
                            seen_companies.add(key)
                            company['yc_batch'] = batch
                            companies.append(company)
                    
                    print(f"[YC-COMPREHENSIVE] Batch {batch}: {len(batch_companies)} companies found")
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"[YC-COMPREHENSIVE] Error scraping batch {batch}: {e}")
                    continue
        
        except ImportError:
            print("[YC-COMPREHENSIVE] YC batch scraper not available, using fallback")
            # Fallback: scrape YC main portfolio page with Playwright
            companies = await self._scrape_yc_main_page()
        
        print(f"[YC-COMPREHENSIVE] Total YC companies found: {len(companies)}")
        return companies
    
    async def _scrape_yc_main_page(self) -> List[Dict]:
        """Fallback: Scrape YC main portfolio page with comprehensive scrolling"""
        companies = []
        seen_companies = set()
        
        if not PLAYWRIGHT_AVAILABLE:
            print("[YC-COMPREHENSIVE] Playwright not available for YC scraping")
            return []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Navigate to YC companies page
                url = "https://www.ycombinator.com/companies"
                print(f"[YC-COMPREHENSIVE] Navigating to {url}...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)
                
                # Infinite scroll to load ALL companies
                previous_count = 0
                no_change_count = 0
                scroll_attempts = 0
                max_scrolls = 1000  # Increased for comprehensive scraping
                
                while scroll_attempts < max_scrolls:
                    # Extract companies from current page
                    page_companies = await page.evaluate("""
                        () => {
                            const companies = [];
                            // Find all company links
                            const links = document.querySelectorAll('a[href*="/companies/"]');
                            links.forEach(link => {
                                const href = link.getAttribute('href');
                                const name = link.textContent.trim();
                                if (name && href) {
                                    companies.push({name: name, href: href});
                                }
                            });
                            return companies;
                        }
                    """)
                    
                    # Process companies
                    for comp in page_companies:
                        name = comp.get('name', '').strip()
                        href = comp.get('href', '')
                        
                        if name and name.lower() not in seen_companies:
                            seen_companies.add(name.lower())
                            
                            # Extract domain from company page
                            domain = await self._extract_yc_company_domain(page, href)
                            
                            companies.append({
                                'name': name,
                                'domain': domain or '',
                                'source': 'yc',
                                'yc_batch': '',  # Will be filled from company page
                                'portfolio_url': urljoin('https://www.ycombinator.com', href)
                            })
                    
                    current_count = len(companies)
                    
                    if scroll_attempts % 10 == 0:
                        print(f"[YC-COMPREHENSIVE] Found {current_count} companies (scroll {scroll_attempts})")
                    
                    # Scroll down
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                    
                    # Check if new content loaded
                    if current_count == previous_count:
                        no_change_count += 1
                        if no_change_count >= 5:
                            print(f"[YC-COMPREHENSIVE] No new companies after {no_change_count} scrolls, stopping")
                            break
                    else:
                        no_change_count = 0
                    
                    previous_count = current_count
                    scroll_attempts += 1
                
                await browser.close()
        
        except Exception as e:
            print(f"[YC-COMPREHENSIVE] Error scraping YC main page: {e}")
            import traceback
            traceback.print_exc()
        
        return companies
    
    async def _extract_yc_company_domain(self, page, href: str) -> Optional[str]:
        """Extract domain from YC company page"""
        try:
            full_url = urljoin('https://www.ycombinator.com', href)
            await page.goto(full_url, wait_until="networkidle", timeout=10000)
            await asyncio.sleep(1)
            
            # Look for website link
            domain = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a[href^="http"]');
                    for (let link of links) {
                        const href = link.getAttribute('href');
                        const text = link.textContent.toLowerCase();
                        if (href && (text.includes('website') || text.includes('visit') || 
                            (!href.includes('ycombinator.com') && !href.includes('twitter') && 
                             !href.includes('linkedin') && !href.includes('github'))) {
                            try {
                                const url = new URL(href);
                                return url.hostname.replace('www.', '');
                            } catch(e) {}
                        }
                    }
                    return null;
                }
            """)
            
            return domain
        except:
            return None
    
    async def scrape_antler_comprehensive(self) -> List[Dict]:
        """
        Comprehensive Antler scraping - ALL companies
        Expected: ~1000+ companies
        """
        companies = []
        seen_companies = set()
        
        if not PLAYWRIGHT_AVAILABLE:
            print("[ANTLER-COMPREHENSIVE] Playwright not available")
            return []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                url = "https://www.antler.co/portfolio"
                print(f"[ANTLER-COMPREHENSIVE] Navigating to {url}...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)
                
                # Infinite scroll to load ALL companies
                previous_count = 0
                no_change_count = 0
                scroll_attempts = 0
                max_scrolls = 500
                
                while scroll_attempts < max_scrolls:
                    # Extract companies from current page
                    page_companies = await page.evaluate("""
                        () => {
                            const companies = [];
                            // Antler uses various selectors
                            const selectors = [
                                '[class*="company"]',
                                '[class*="portfolio"]',
                                '[class*="startup"]',
                                'a[href*="/portfolio/"]',
                                'a[href*="/companies/"]'
                            ];
                            
                            selectors.forEach(selector => {
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(elem => {
                                    const name = elem.textContent.trim();
                                    const href = elem.getAttribute('href') || '';
                                    if (name && name.length > 2 && name.length < 100) {
                                        companies.push({name: name, href: href});
                                    }
                                });
                            });
                            
                            return companies;
                        }
                    """)
                    
                    # Process companies
                    for comp in page_companies:
                        name = comp.get('name', '').strip()
                        href = comp.get('href', '')
                        
                        if name and name.lower() not in seen_companies:
                            seen_companies.add(name.lower())
                            
                            # Extract domain
                            domain = None
                            if href:
                                domain = await self._extract_domain_from_url(href)
                            
                            if not domain:
                                domain = await self._discover_domain_from_name(name)
                            
                            companies.append({
                                'name': name,
                                'domain': domain or '',
                                'source': 'antler',
                                'portfolio_url': urljoin('https://www.antler.co', href) if href else url
                            })
                    
                    current_count = len(companies)
                    
                    if scroll_attempts % 10 == 0:
                        print(f"[ANTLER-COMPREHENSIVE] Found {current_count} companies (scroll {scroll_attempts})")
                    
                    # Scroll down
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                    
                    if current_count == previous_count:
                        no_change_count += 1
                        if no_change_count >= 5:
                            break
                    else:
                        no_change_count = 0
                    
                    previous_count = current_count
                    scroll_attempts += 1
                
                await browser.close()
        
        except Exception as e:
            print(f"[ANTLER-COMPREHENSIVE] Error: {e}")
            import traceback
            traceback.print_exc()
        
        return companies
    
    async def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain = domain.replace('www.', '').split('/')[0]
            if domain and '.' in domain:
                return domain.lower()
        except:
            pass
        return None
    
    async def _discover_domain_from_name(self, company_name: str) -> Optional[str]:
        """Try to discover domain from company name"""
        if not company_name or len(company_name) < 2:
            return None
        
        clean_name = re.sub(r'[^\w\s-]', '', company_name.lower().strip())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        potential_domains = []
        no_spaces = clean_name.replace(' ', '').replace('-', '')
        
        # Common TLDs
        for tld in ['.com', '.io', '.ai', '.co']:
            potential_domains.append(f"{no_spaces}{tld}")
            potential_domains.append(f"{clean_name.replace(' ', '-')}{tld}")
        
        # Try validating (limit to top 3)
        session = await self._get_session()
        for domain in potential_domains[:3]:
            try:
                async with session.get(
                    f"https://{domain}",
                    timeout=aiohttp.ClientTimeout(total=2),
                    allow_redirects=True,
                    ssl=False
                ) as response:
                    if response.status < 400:
                        return domain
            except:
                continue
        
        # Return most likely candidate
        return potential_domains[0] if potential_domains else None
    
    async def scrape_all_vcs(self, db_conn) -> Dict[str, List[Dict]]:
        """
        Scrape ALL VCs in database
        Returns dict mapping VC firm_name to list of companies
        """
        results = {}
        
        # Get all VCs from database
        vc_results = db_conn.execute("""
            SELECT firm_name, portfolio_url, url, type 
            FROM vcs 
            WHERE portfolio_url IS NOT NULL OR url IS NOT NULL
            ORDER BY firm_name
        """).fetchall()
        
        print(f"[ALL-VCS] Found {len(vc_results)} VCs to scrape")
        
        for idx, row in enumerate(vc_results):
            firm_name = row[0]
            portfolio_url = row[1] or row[2]
            vc_type = row[3] or 'VC'
            
            print(f"[ALL-VCS] [{idx+1}/{len(vc_results)}] Scraping {firm_name}...")
            
            try:
                # Use enhanced scraper for generic portfolios
                from portfolio_scraper_enhanced import EnhancedPortfolioScraper, PortfolioConfig
                
                scraper = EnhancedPortfolioScraper()
                
                # Create config based on VC type
                config = PortfolioConfig(
                    name=firm_name,
                    url=portfolio_url,
                    scroll_type="infinite",  # Most portfolios use infinite scroll
                    max_companies=10000,  # No limit
                    max_scroll_attempts=1000,
                    scroll_wait_time=2.0
                )
                
                companies = await scraper.scrape_portfolio(config)
                results[firm_name] = companies
                
                print(f"[ALL-VCS] {firm_name}: {len(companies)} companies found")
                
            except Exception as e:
                print(f"[ALL-VCS] Error scraping {firm_name}: {e}")
                results[firm_name] = []
                continue
        
        return results


async def main():
    """Test comprehensive scraping"""
    scraper = ComprehensivePortfolioScraper()
    
    print("=" * 80)
    print("COMPREHENSIVE PORTFOLIO SCRAPING - SCALING TEST")
    print("=" * 80)
    
    # Test YC
    print("\n1. Testing YC Comprehensive Scraping...")
    yc_companies = await scraper.scrape_yc_comprehensive()
    print(f"YC Result: {len(yc_companies)} companies")
    
    # Test Antler
    print("\n2. Testing Antler Comprehensive Scraping...")
    antler_companies = await scraper.scrape_antler_comprehensive()
    print(f"Antler Result: {len(antler_companies)} companies")
    
    await scraper.close_session()
    
    print("\n" + "=" * 80)
    print(f"TOTAL COMPANIES: {len(yc_companies) + len(antler_companies)}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())



