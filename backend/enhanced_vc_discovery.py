"""
Enhanced VC Discovery System - Comprehensive Early-Stage Investor Discovery
Discovers ALL active VCs, Venture Studios, Incubators, and Accelerators
"""
import asyncio
import re
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urlparse

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class EnhancedVCDiscovery:
    """Comprehensive VC discovery system for ALL early-stage investors"""
    
    # Comprehensive list of VC directory sources
    VC_DIRECTORY_SOURCES = [
        # Major VC Directories
        "https://www.cbinsights.com/research-venture-capital-firms",
        "https://www.crunchbase.com/discover/organization.companies/venture_capital",
        "https://www.pitchbook.com/profiles/firm-type/venture-capital",
        "https://www.thevc.com/",
        "https://www.vc-list.com/",
        "https://www.angellist.com/venture-capital",
        
        # Accelerator Directories
        "https://www.seed-db.com/accelerators",
        "https://www.f6s.com/accelerators",
        "https://www.techstars.com/accelerators",
        
        # Venture Studio Directories
        "https://www.venturestudioindex.com/",
        "https://www.studio.vc/",
        
        # Regional VC Lists
        "https://www.svb.com/venture-capital-directory",
        "https://www.nvca.org/members/",
        
        # Early-Stage Focused
        "https://www.seedcamp.com/",
        "https://www.500.co/",
    ]
    
    # Search queries for web discovery
    SEARCH_QUERIES = [
        "top seed stage venture capital firms",
        "best pre-seed investors",
        "early stage VC firms",
        "venture studios list",
        "startup accelerators",
        "incubators directory",
        "seed investors directory",
        "pre-seed funding firms",
    ]
    
    # Known comprehensive VC lists (curated)
    KNOWN_VC_LISTS = [
        # Top VCs
        "https://www.cbinsights.com/research/top-venture-capital-partners",
        "https://www.forbes.com/lists/best-venture-capital-firms/",
        
        # Accelerators
        "https://www.ycombinator.com/accelerators",
        "https://www.techstars.com/accelerators",
        
        # Studios
        "https://www.venturestudioindex.com/studios",
    ]
    
    def __init__(self):
        self.session = None
        self.discovered_vcs = []
        self.seen_firms = set()
    
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
    
    async def discover_all_comprehensive(self) -> List[Dict]:
        """
        Comprehensive discovery from ALL sources
        Returns list of ALL discovered VCs, Studios, Accelerators, Incubators
        """
        print("\n" + "="*80)
        print("COMPREHENSIVE VC DISCOVERY - ALL EARLY-STAGE INVESTORS")
        print("="*80 + "\n")
        
        all_vcs = []
        
        # Method 1: Directory crawling
        print("[METHOD 1] Crawling VC directories...")
        directory_vcs = await self.discover_from_directories()
        all_vcs.extend(directory_vcs)
        print(f"Found {len(directory_vcs)} VCs from directories")
        
        # Method 2: Known VC lists
        print("\n[METHOD 2] Scraping known VC lists...")
        list_vcs = await self.discover_from_known_lists()
        all_vcs.extend(list_vcs)
        print(f"Found {len(list_vcs)} VCs from known lists")
        
        # Method 3: Web search discovery (if available)
        print("\n[METHOD 3] Web search discovery...")
        search_vcs = await self.discover_from_web_search()
        all_vcs.extend(search_vcs)
        print(f"Found {len(search_vcs)} VCs from web search")
        
        # Method 4: Portfolio page discovery (find VCs by their portfolio pages)
        print("\n[METHOD 4] Portfolio page discovery...")
        portfolio_vcs = await self.discover_from_portfolio_pages()
        all_vcs.extend(portfolio_vcs)
        print(f"Found {len(portfolio_vcs)} VCs from portfolio pages")
        
        # Deduplicate
        unique_vcs = self._deduplicate_vcs(all_vcs)
        
        # Categorize each VC
        print("\n[Categorizing VCs...]")
        categorized_vcs = []
        for vc in unique_vcs:
            categorized = await self.categorize_vc(vc)
            categorized_vcs.append(categorized)
        
        print(f"\n{'='*80}")
        print(f"TOTAL DISCOVERED: {len(categorized_vcs)} unique VCs/Studios/Accelerators")
        print(f"{'='*80}\n")
        
        return categorized_vcs
    
    async def discover_from_directories(self) -> List[Dict]:
        """Discover from VC directory websites"""
        discovered = []
        
        if CRAWL4AI_AVAILABLE:
            browser_config = BrowserConfig(headless=True, verbose=False)
            crawler_config = CrawlerRunConfig(
                wait_for_images=False,
                process_iframes=False,
                wait_for="domcontentloaded",
                page_timeout=30000
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for idx, url in enumerate(self.VC_DIRECTORY_SOURCES):
                    try:
                        print(f"  [{idx+1}/{len(self.VC_DIRECTORY_SOURCES)}] {url}")
                        result = await crawler.arun(url=url, config=crawler_config)
                        
                        if result.success and result.html:
                            soup = BeautifulSoup(result.html, 'html.parser')
                            vcs = self._extract_vcs_from_page(soup, url)
                            discovered.extend(vcs)
                            print(f"    Found {len(vcs)} VCs")
                    except Exception as e:
                        print(f"    Error: {e}")
                        continue
        
        return discovered
    
    async def discover_from_known_lists(self) -> List[Dict]:
        """Discover from known comprehensive VC lists"""
        discovered = []
        
        if CRAWL4AI_AVAILABLE:
            browser_config = BrowserConfig(headless=True, verbose=False)
            crawler_config = CrawlerRunConfig(
                wait_for_images=False,
                process_iframes=False,
                wait_for="domcontentloaded",
                page_timeout=30000
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for url in self.KNOWN_VC_LISTS:
                    try:
                        result = await crawler.arun(url=url, config=crawler_config)
                        if result.success and result.html:
                            soup = BeautifulSoup(result.html, 'html.parser')
                            vcs = self._extract_vcs_from_page(soup, url)
                            discovered.extend(vcs)
                    except:
                        continue
        
        return discovered
    
    async def discover_from_web_search(self) -> List[Dict]:
        """Discover VCs through web search (placeholder - would use search API)"""
        # In production, would use Google Search API, Bing API, etc.
        # For now, return empty - can be enhanced with actual search APIs
        return []
    
    async def discover_from_portfolio_pages(self) -> List[Dict]:
        """Discover VCs by finding portfolio pages on the web"""
        discovered = []
        
        # Common portfolio page patterns
        portfolio_patterns = [
            "/portfolio",
            "/companies",
            "/investments",
            "/startups",
            "/portfolio-companies"
        ]
        
        # This would require web crawling to find pages matching these patterns
        # For now, return empty - can be enhanced with web crawling
        
        return discovered
    
    def _extract_vcs_from_page(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """Extract VC information from a page"""
        vcs = []
        
        # Strategy 1: Find VC links
        vc_links = soup.find_all('a', href=re.compile(
            r'vc|venture|capital|fund|invest|accelerator|studio|incubator', re.I
        ))
        
        for link in vc_links:
            firm_name = link.get_text(strip=True)
            href = link.get('href', '')
            
            if firm_name and 3 < len(firm_name) < 100:
                # Skip common non-VC terms
                skip_terms = ['learn more', 'read more', 'view', 'click', 'here', 'more', 'apply']
                if any(term in firm_name.lower() for term in skip_terms):
                    continue
                
                name_key = firm_name.lower().strip()
                if name_key in self.seen_firms:
                    continue
                self.seen_firms.add(name_key)
                
                # Extract domain
                domain = self._extract_domain(href)
                if not domain and href.startswith('http'):
                    domain = self._extract_domain(href)
                
                # Build URL
                if href.startswith('http'):
                    url = href
                elif domain:
                    url = f"https://{domain}"
                else:
                    continue
                
                vcs.append({
                    'firm_name': firm_name,
                    'url': url,
                    'domain': domain,
                    'discovered_from': source_url,
                    'type': 'VC'  # Will be categorized later
                })
        
        # Strategy 2: Find firm names in structured data
        # Look for JSON-LD, microdata, etc.
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Extract organization data
                    if data.get('@type') == 'Organization':
                        firm_name = data.get('name', '')
                        url = data.get('url', '')
                        if firm_name and url:
                            name_key = firm_name.lower().strip()
                            if name_key not in self.seen_firms:
                                self.seen_firms.add(name_key)
                                domain = self._extract_domain(url)
                                vcs.append({
                                    'firm_name': firm_name,
                                    'url': url,
                                    'domain': domain,
                                    'discovered_from': source_url,
                                    'type': 'VC'
                                })
            except:
                continue
        
        return vcs
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain = domain.replace('www.', '').split('/')[0]
            return domain.lower()
        except:
            return ""
    
    def _deduplicate_vcs(self, vcs: List[Dict]) -> List[Dict]:
        """Remove duplicate VCs"""
        seen = set()
        unique = []
        
        for vc in vcs:
            # Use firm_name as key
            key = vc.get('firm_name', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(vc)
        
        return unique
    
    async def categorize_vc(self, vc: Dict) -> Dict:
        """Categorize VC by type, stage, and focus areas"""
        url = vc.get('url', '')
        firm_name = vc.get('firm_name', '').lower()
        
        # Determine type from name/URL
        vc_type = 'VC'
        if 'accelerator' in firm_name or 'accelerator' in url:
            vc_type = 'Accelerator'
        elif 'studio' in firm_name or 'studio' in url:
            vc_type = 'Studio'
        elif 'incubator' in firm_name or 'incubator' in url:
            vc_type = 'Incubator'
        
        # Determine stage
        stage = 'Unknown'
        if 'pre-seed' in firm_name or 'preseed' in firm_name:
            stage = 'Pre-Seed'
        elif 'seed' in firm_name:
            stage = 'Seed'
        elif 'series a' in firm_name or 'series-a' in firm_name:
            stage = 'Series A'
        
        # Try to get more info from website
        if url:
            try:
                session = await self._get_session()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text().lower()
                        
                        # Refine type
                        if 'accelerator' in text:
                            vc_type = 'Accelerator'
                        elif 'venture studio' in text or 'studio' in text:
                            vc_type = 'Studio'
                        elif 'incubator' in text:
                            vc_type = 'Incubator'
                        
                        # Refine stage
                        if 'pre-seed' in text or 'preseed' in text:
                            stage = 'Pre-Seed'
                        elif 'seed' in text and 'series' not in text:
                            stage = 'Seed'
                        elif 'series a' in text:
                            stage = 'Series A'
            except:
                pass
        
        vc['type'] = vc_type
        vc['stage'] = stage
        vc['focus_areas'] = []  # Can be enhanced
        
        return vc


async def main():
    """Test comprehensive VC discovery"""
    discovery = EnhancedVCDiscovery()
    
    try:
        vcs = await discovery.discover_all_comprehensive()
        
        print("\n" + "="*80)
        print("DISCOVERY RESULTS")
        print("="*80)
        
        # Group by type
        by_type = {}
        for vc in vcs:
            vc_type = vc.get('type', 'VC')
            if vc_type not in by_type:
                by_type[vc_type] = []
            by_type[vc_type].append(vc)
        
        for vc_type, type_vcs in by_type.items():
            print(f"\n{vc_type}: {len(type_vcs)}")
            for vc in type_vcs[:5]:  # Show first 5
                print(f"  - {vc['firm_name']} ({vc.get('domain', 'N/A')})")
            if len(type_vcs) > 5:
                print(f"  ... and {len(type_vcs) - 5} more")
        
        print(f"\n{'='*80}")
        print(f"TOTAL: {len(vcs)} VCs/Studios/Accelerators discovered")
        print(f"{'='*80}\n")
        
    finally:
        await discovery.close_session()


if __name__ == "__main__":
    asyncio.run(main())



