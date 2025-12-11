"""
Celerio Scout - VC Discovery System
Automatically discovers and categorizes VC firms from web sources
"""
import asyncio
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import aiohttp

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False


class VCDiscovery:
    """Discovers VC firms from various web sources"""
    
    # Known VC directory websites
    VC_DIRECTORIES = [
        "https://www.crunchbase.com/discover/organization.companies/venture_capital",
        "https://www.pitchbook.com/profiles/firm-type/venture-capital",
    ]
    
    # Focus area keywords for categorization
    FOCUS_KEYWORDS = {
        "AI/ML": ["artificial intelligence", "machine learning", "ai", "ml", "deep learning", "neural", "llm", "gpt"],
        "B2B SaaS": ["b2b", "saas", "enterprise", "business software", "b2b saas"],
        "Fintech": ["fintech", "financial technology", "payments", "banking", "crypto", "blockchain"],
        "Healthcare": ["healthcare", "health tech", "medtech", "biotech", "pharma"],
        "Consumer": ["consumer", "b2c", "retail", "e-commerce", "marketplace"],
        "Enterprise": ["enterprise", "b2b enterprise", "corporate software"],
        "DevTools": ["developer tools", "devtools", "infrastructure", "platform"],
        "Security": ["cybersecurity", "security", "privacy", "compliance"],
        "Climate": ["climate", "clean tech", "sustainability", "energy"],
    }
    
    # Stage keywords
    STAGE_KEYWORDS = {
        "Pre-Seed": ["pre-seed", "pre seed", "idea stage", "concept"],
        "Seed": ["seed", "seed stage", "early stage"],
        "Series A": ["series a", "series-a", "series_a"],
        "Series B": ["series b", "series-b", "series_b"],
        "Growth": ["growth", "late stage", "growth stage"],
    }
    
    async def discover_from_crunchbase(self) -> List[Dict]:
        """Discover VCs from Crunchbase (mock - would need API access)"""
        # In production, would use Crunchbase API or scrape their directory
        return []
    
    async def discover_from_pitchbook(self) -> List[Dict]:
        """Discover VCs from Pitchbook (mock - would need API access)"""
        # In production, would use Pitchbook API
        return []
    
    async def discover_from_vc_lists(self) -> List[Dict]:
        """Discover VCs from curated lists and directories - comprehensive crawl"""
        discovered = []
        seen_firms = set()
        
        # Comprehensive list of VC directory and list websites
        sources = [
            {
                "url": "https://www.cbinsights.com/research-venture-capital-firms",
                "type": "directory",
                "pattern": r'venture|capital|vc|fund'
            },
            {
                "url": "https://www.thevc.com/",
                "type": "directory",
                "pattern": r'vc|venture|capital'
            },
            {
                "url": "https://www.vcnewsdaily.com/",
                "type": "news",
                "pattern": r'vc|venture|capital'
            },
            {
                "url": "https://www.vc-list.com/",
                "type": "directory",
                "pattern": r'vc|venture|capital'
            },
            {
                "url": "https://www.angellist.com/venture-capital",
                "type": "directory",
                "pattern": r'venture|capital|vc'
            },
        ]
        
        # Also search common VC listing pages
        search_queries = [
            "top venture capital firms",
            "best VC firms",
            "venture capital directory",
            "startup accelerators list",
            "venture studios"
        ]
        
        print(f"Starting VC discovery from {len(sources)} sources...")
        
        if CRAWL4AI_AVAILABLE:
            try:
                browser_config = BrowserConfig(headless=True, verbose=False)
                # Use more lenient timeout and wait conditions
                crawler_config = CrawlerRunConfig(
                    wait_for_images=False, 
                    process_iframes=False,
                    wait_for="networkidle",  # Changed from domcontentloaded to networkidle for better reliability
                    page_timeout=30000,  # Increased from 20000 to 30000ms (30 seconds)
                    wait_for_timeout=30000  # Explicit timeout for wait condition
                )
                
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    for idx, source in enumerate(sources):
                        try:
                            print(f"[{idx+1}/{len(sources)}] Crawling {source['url']}...")
                            
                            # Try crawling with retry logic
                            result = None
                            max_retries = 2
                            for retry in range(max_retries):
                                try:
                                    result = await crawler.arun(url=source["url"], config=crawler_config)
                                    if result.success:
                                        break
                                except RuntimeError as e:
                                    if "Timeout" in str(e) or "Wait condition failed" in str(e):
                                        if retry < max_retries - 1:
                                            print(f"  [WARN] Timeout on attempt {retry + 1}, retrying with shorter timeout...")
                                            # Use shorter timeout on retry
                                            retry_config = CrawlerRunConfig(
                                                wait_for_images=False,
                                                process_iframes=False,
                                                wait_for="load",  # More lenient wait condition
                                                page_timeout=15000,
                                                wait_for_timeout=15000
                                            )
                                            result = await crawler.arun(url=source["url"], config=retry_config)
                                            if result.success:
                                                break
                                        else:
                                            print(f"  [ERROR] Failed after {max_retries} attempts: {e}")
                                            result = None
                                    else:
                                        raise  # Re-raise if it's not a timeout error
                            
                            if result and result.success and result.html:
                                soup = BeautifulSoup(result.html, 'html.parser')
                                
                                # Look for VC firm links with various patterns
                                vc_links = soup.find_all('a', href=re.compile(
                                    r'vc|venture|capital|fund|invest|accelerator|studio', re.I
                                ))
                                
                                # Also look for firm names in headings and divs
                                firm_elements = soup.find_all(['h1', 'h2', 'h3', 'div', 'span'],
                                    class_=re.compile(r'firm|company|vc|venture', re.I))
                                
                                for link in vc_links[:100]:  # Increased limit
                                    firm_name = link.get_text(strip=True)
                                    href = link.get('href', '')
                                    
                                    if firm_name and len(firm_name) > 2 and len(firm_name) < 100:
                                        # Skip common non-VC terms
                                        skip_terms = ['learn more', 'read more', 'view', 'click', 'here', 'more']
                                        if any(term in firm_name.lower() for term in skip_terms):
                                            continue
                                        
                                        name_key = firm_name.lower().strip()
                                        if name_key in seen_firms:
                                            continue
                                        seen_firms.add(name_key)
                                        
                                        # Try to extract domain from href
                                        domain = self._extract_domain(href)
                                        
                                        # Build full URL
                                        if href.startswith('http'):
                                            url = href
                                        elif domain:
                                            url = f"https://{domain}"
                                        else:
                                            continue
                                        
                                        discovered.append({
                                            'firm_name': firm_name,
                                            'url': url,
                                            'domain': domain,
                                            'discovered_from': source["url"],
                                            'type': 'VC'  # Default, will be refined
                                        })
                                
                                # Process firm elements
                                for elem in firm_elements[:50]:
                                    firm_name = elem.get_text(strip=True)
                                    if firm_name and 3 < len(firm_name) < 100:
                                        name_key = firm_name.lower().strip()
                                        if name_key not in seen_firms:
                                            seen_firms.add(name_key)
                                            # Try to find link nearby
                                            link_elem = elem.find('a', href=re.compile(r'^https?://'))
                                            if link_elem:
                                                href = link_elem.get('href', '')
                                                domain = self._extract_domain(href)
                                                discovered.append({
                                                    'firm_name': firm_name,
                                                    'url': href,
                                                    'domain': domain,
                                                    'discovered_from': source["url"],
                                                    'type': 'VC'
                                                })
                        except RuntimeError as e:
                            error_msg = str(e)
                            if "Timeout" in error_msg or "Wait condition failed" in error_msg:
                                print(f"  [WARN] Timeout crawling {source['url']} - skipping (this is normal for some sites)")
                            else:
                                print(f"  [ERROR] Runtime error crawling {source['url']}: {error_msg[:200]}")
                            continue
                        except Exception as e:
                            error_msg = str(e)
                            print(f"  [ERROR] Error discovering from {source['url']}: {error_msg[:200]}")
                            continue
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] VC discovery crawler error: {error_msg[:200]}")
                print("[INFO] Continuing with fallback discovery methods...")
        
        # Also try web search approach using common VC firm patterns
        # This is a fallback if direct crawling doesn't work
        if len(discovered) < 10:
            print("Trying alternative discovery methods...")
            # Add known VC firms from common knowledge
            known_vcs = [
                {'firm_name': 'Accel', 'url': 'https://www.accel.com/', 'domain': 'accel.com'},
                {'firm_name': 'Greylock Partners', 'url': 'https://www.greylock.com/', 'domain': 'greylock.com'},
                {'firm_name': 'Index Ventures', 'url': 'https://www.indexventures.com/', 'domain': 'indexventures.com'},
                {'firm_name': 'General Catalyst', 'url': 'https://www.generalcatalyst.com/', 'domain': 'generalcatalyst.com'},
                {'firm_name': 'Insight Partners', 'url': 'https://www.insightpartners.com/', 'domain': 'insightpartners.com'},
                {'firm_name': 'Bessemer Venture Partners', 'url': 'https://www.bvp.com/', 'domain': 'bvp.com'},
                {'firm_name': 'GV (Google Ventures)', 'url': 'https://www.gv.com/', 'domain': 'gv.com'},
                {'firm_name': 'Khosla Ventures', 'url': 'https://www.khoslaventures.com/', 'domain': 'khoslaventures.com'},
                {'firm_name': 'NEA', 'url': 'https://www.nea.com/', 'domain': 'nea.com'},
                {'firm_name': 'Redpoint Ventures', 'url': 'https://www.redpoint.com/', 'domain': 'redpoint.com'},
            ]
            
            for vc in known_vcs:
                name_key = vc['firm_name'].lower()
                if name_key not in seen_firms:
                    seen_firms.add(name_key)
                    discovered.append({
                        'firm_name': vc['firm_name'],
                        'url': vc['url'],
                        'domain': vc['domain'],
                        'discovered_from': 'known_list',
                        'type': 'VC'
                    })
        
        print(f"Discovered {len(discovered)} VCs total")
        return discovered
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        
        # Remove protocol
        url = url.replace('https://', '').replace('http://', '')
        # Remove path
        url = url.split('/')[0]
        # Remove www
        url = url.replace('www.', '')
        
        return url
    
    async def categorize_vc(self, vc: Dict) -> Dict:
        """Categorize VC by stage and focus areas"""
        # Get VC website content
        url = vc.get('url', '')
        if not url:
            return vc
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text().lower()
                        
                        # Determine stage
                        stage = self._determine_stage(text, vc.get('firm_name', ''))
                        
                        # Determine focus areas
                        focus_areas = self._determine_focus_areas(text)
                        
                        # Determine type
                        vc_type = self._determine_type(text, vc.get('firm_name', ''))
                        
                        vc['stage'] = stage
                        vc['focus_areas'] = focus_areas
                        vc['type'] = vc_type
                        
        except Exception as e:
            print(f"Error categorizing VC {vc.get('firm_name')}: {e}")
            # Set defaults
            vc['stage'] = 'Unknown'
            vc['focus_areas'] = []
            vc['type'] = vc.get('type', 'VC')
        
        return vc
    
    def _determine_stage(self, text: str, firm_name: str) -> str:
        """Determine investment stage from text"""
        text_lower = text.lower()
        firm_lower = firm_name.lower()
        
        # Check for stage keywords
        for stage, keywords in self.STAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower or keyword in firm_lower:
                    return stage
        
        # Default based on common patterns
        if 'accelerator' in text_lower or 'accelerator' in firm_lower:
            return 'Pre-Seed/Seed'
        if 'studio' in text_lower or 'studio' in firm_lower:
            return 'Pre-Seed/Seed'
        
        return 'Unknown'
    
    def _determine_focus_areas(self, text: str) -> List[str]:
        """Determine focus areas from text"""
        text_lower = text.lower()
        focus_areas = []
        
        for focus, keywords in self.FOCUS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    focus_areas.append(focus)
                    break  # Only add once per focus area
        
        return focus_areas if focus_areas else ['General']
    
    def _determine_type(self, text: str, firm_name: str) -> str:
        """Determine VC type"""
        text_lower = text.lower()
        firm_lower = firm_name.lower()
        
        if 'accelerator' in text_lower or 'accelerator' in firm_lower:
            return 'Accelerator'
        if 'studio' in text_lower or 'studio' in firm_lower:
            return 'Studio'
        if 'fund' in text_lower or 'capital' in firm_lower:
            return 'VC'
        
        return 'VC'
    
    async def discover_all(self) -> List[Dict]:
        """Discover VCs from all sources"""
        all_vcs = []
        
        # Discover from various sources
        vc_lists = await self.discover_from_vc_lists()
        all_vcs.extend(vc_lists)
        
        # Categorize each VC
        categorized_vcs = []
        for vc in all_vcs:
            categorized = await self.categorize_vc(vc)
            categorized_vcs.append(categorized)
        
        return categorized_vcs

