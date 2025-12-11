"""
Celerio Scout - VC Discovery System
Automatically discovers and categorizes VC firms from web sources
Comprehensive multi-layered discovery system
"""
import asyncio
import re
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urlparse, urljoin, quote_plus
import json

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

# Try to import Google Search API
try:
    from googlesearch import search as google_search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False


class VCDiscovery:
    """Discovers VC firms from various web sources - Comprehensive multi-layered system"""
    
    def __init__(self):
        self.seen_firms: Set[str] = set()
        self.seen_domains: Set[str] = set()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize firm name for deduplication"""
        if not name:
            return ""
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        for suffix in [' llc', ' inc', ' ltd', ' limited', ' corp', ' corporation']:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        return normalized
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            domain = domain.replace('www.', '').lower()
            return domain
        except:
            return ""
    
    def _is_duplicate(self, vc: Dict) -> bool:
        """Check if VC is duplicate"""
        firm_name = vc.get('firm_name', '').strip()
        domain = vc.get('domain', '').strip()
        
        if not firm_name:
            return True
        
        normalized_name = self._normalize_name(firm_name)
        
        if normalized_name in self.seen_firms:
            return True
        
        if domain and domain in self.seen_domains:
            return True
        
        if not domain:
            url = vc.get('url', '')
            domain = self._extract_domain(url)
            if domain and domain in self.seen_domains:
                return True
        
        self.seen_firms.add(normalized_name)
        if domain:
            self.seen_domains.add(domain)
        
        return False
    
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
    
    async def discover_from_crunchbase_comprehensive(self) -> List[Dict]:
        """Comprehensive Crunchbase discovery - multiple pages"""
        discovered = []
        seen_firms = set()
        
        # Crunchbase VC directory pages (multiple pages for comprehensive coverage)
        base_url = "https://www.crunchbase.com/discover/organization.companies/venture_capital"
        pages_to_scrape = 10  # Start with 10 pages, can expand
        
        print(f"[CRUNCHBASE] Starting comprehensive discovery ({pages_to_scrape} pages)...")
        
        if CRAWL4AI_AVAILABLE:
            try:
                browser_config = BrowserConfig(headless=True, verbose=False)
                crawler_config = CrawlerRunConfig(
                    wait_for_images=False,
                    process_iframes=False,
                    wait_for="networkidle",
                    page_timeout=30000,
                    wait_for_timeout=30000
                )
                
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    for page in range(1, pages_to_scrape + 1):
                        try:
                            url = f"{base_url}?page={page}" if page > 1 else base_url
                            print(f"  [Page {page}/{pages_to_scrape}] Crawling {url}...")
                            
                            result = await crawler.arun(url=url, config=crawler_config)
                            
                            if result.success and result.html:
                                soup = BeautifulSoup(result.html, 'html.parser')
                                
                                # Crunchbase structure: Look for organization links
                                org_links = soup.find_all('a', href=re.compile(r'/organization/'))
                                
                                page_count = 0
                                for link in org_links[:200]:  # Limit per page
                                    firm_name = link.get_text(strip=True)
                                    href = link.get('href', '')
                                    
                                    if firm_name and len(firm_name) > 2 and len(firm_name) < 100:
                                        name_key = firm_name.lower().strip()
                                        if name_key in seen_firms:
                                            continue
                                        seen_firms.add(name_key)
                                        
                                        if href.startswith('/'):
                                            href = f"https://www.crunchbase.com{href}"
                                        
                                        domain = self._extract_domain(href)
                                        
                                        discovered.append({
                                            'firm_name': firm_name,
                                            'url': href,
                                            'domain': domain,
                                            'discovered_from': 'crunchbase',
                                            'type': 'VC'
                                        })
                                        page_count += 1
                                
                                print(f"    Found {page_count} VCs on page {page}")
                                
                                if page_count == 0:
                                    print(f"    [INFO] No VCs found on page {page}, stopping pagination")
                                    break
                            
                            await asyncio.sleep(3)  # Rate limiting
                            
                        except RuntimeError as e:
                            error_msg = str(e)
                            if "Timeout" in error_msg:
                                print(f"  [WARN] Timeout on page {page}, continuing...")
                            else:
                                print(f"  [ERROR] Error on page {page}: {error_msg[:200]}")
                            continue
                        except Exception as e:
                            print(f"  [ERROR] Error crawling page {page}: {e}")
                            continue
            
            except Exception as e:
                print(f"[ERROR] Crunchbase discovery error: {e}")
        
        print(f"[CRUNCHBASE] Discovered {len(discovered)} VCs total")
        return discovered
    
    async def discover_from_f6s_accelerators(self) -> List[Dict]:
        """Discover Accelerators from F6S (largest accelerator database)"""
        discovered = []
        seen_firms = set()
        
        base_url = "https://www.f6s.com/accelerators"
        pages_to_scrape = 20  # F6S has many pages
        
        print(f"[F6S] Starting accelerator discovery ({pages_to_scrape} pages)...")
        
        if CRAWL4AI_AVAILABLE:
            try:
                browser_config = BrowserConfig(headless=True, verbose=False)
                crawler_config = CrawlerRunConfig(
                    wait_for_images=False,
                    process_iframes=False,
                    wait_for="networkidle",
                    page_timeout=30000
                )
                
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    for page in range(1, pages_to_scrape + 1):
                        try:
                            url = f"{base_url}?page={page}" if page > 1 else base_url
                            print(f"  [Page {page}/{pages_to_scrape}] Crawling {url}...")
                            
                            result = await crawler.arun(url=url, config=crawler_config)
                            
                            if result.success and result.html:
                                soup = BeautifulSoup(result.html, 'html.parser')
                                
                                # F6S structure: Look for accelerator links
                                accelerator_links = soup.find_all('a', href=re.compile(r'/accelerator/|/program/'))
                                
                                page_count = 0
                                for link in accelerator_links[:100]:
                                    firm_name = link.get_text(strip=True)
                                    href = link.get('href', '')
                                    
                                    if firm_name and len(firm_name) > 2:
                                        name_key = firm_name.lower().strip()
                                        if name_key in seen_firms:
                                            continue
                                        seen_firms.add(name_key)
                                        
                                        if href.startswith('/'):
                                            href = f"https://www.f6s.com{href}"
                                        
                                        domain = self._extract_domain(href)
                                        
                                        discovered.append({
                                            'firm_name': firm_name,
                                            'url': href,
                                            'domain': domain,
                                            'discovered_from': 'f6s',
                                            'type': 'Accelerator'
                                        })
                                        page_count += 1
                                
                                print(f"    Found {page_count} accelerators on page {page}")
                                
                                if page_count == 0:
                                    break
                            
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            print(f"  [ERROR] Error on page {page}: {e}")
                            continue
            
            except Exception as e:
                print(f"[ERROR] F6S discovery error: {e}")
        
        print(f"[F6S] Discovered {len(discovered)} accelerators total")
        return discovered
    
    async def discover_all(self) -> List[Dict]:
        """Discover VCs from all sources - COMPREHENSIVE"""
        all_vcs = []
        
        print("\n" + "="*80)
        print("COMPREHENSIVE VC DISCOVERY - ALL INVESTMENT VEHICLES")
        print("="*80 + "\n")
        
        # Layer 1: Crunchbase (VCs) - Comprehensive
        try:
            print("[LAYER 1] Crunchbase VC Discovery...")
            crunchbase_vcs = await self.discover_from_crunchbase_comprehensive()
            all_vcs.extend(crunchbase_vcs)
            print(f"[SUCCESS] Crunchbase: {len(crunchbase_vcs)} VCs\n")
        except Exception as e:
            print(f"[ERROR] Crunchbase discovery failed: {e}\n")
        
        # Layer 2: F6S (Accelerators) - Comprehensive
        try:
            print("[LAYER 2] F6S Accelerator Discovery...")
            f6s_accelerators = await self.discover_from_f6s_accelerators()
            all_vcs.extend(f6s_accelerators)
            print(f"[SUCCESS] F6S: {len(f6s_accelerators)} Accelerators\n")
        except Exception as e:
            print(f"[ERROR] F6S discovery failed: {e}\n")
        
        # Layer 2.5: StudioHub (Studios) - Comprehensive
        try:
            print("[LAYER 2.5] StudioHub Studio Discovery...")
            studiohub_studios = await self.discover_from_studiohub()
            all_vcs.extend(studiohub_studios)
            print(f"[SUCCESS] StudioHub: {len(studiohub_studios)} Studios\n")
        except Exception as e:
            print(f"[ERROR] StudioHub discovery failed: {e}\n")
        
        # Layer 3: Existing VC lists discovery
        try:
            print("[LAYER 3] VC Directory Lists Discovery...")
            vc_lists = await self.discover_from_vc_lists()
            all_vcs.extend(vc_lists)
            print(f"[SUCCESS] Directories: {len(vc_lists)} investment vehicles\n")
        except Exception as e:
            print(f"[ERROR] Directory discovery failed: {e}\n")
        
        # Layer 4: Google Search Discovery
        try:
            print("[LAYER 4] Google Search Discovery...")
            search_queries = [
                "venture capital firms directory",
                "top VC firms",
                "venture studios list",
                "startup accelerators directory",
            ]
            google_results = await self.discover_from_google_search(search_queries, max_results_per_query=30)
            all_vcs.extend(google_results)
            print(f"[SUCCESS] Google Search: {len(google_results)} investment vehicles\n")
        except Exception as e:
            print(f"[ERROR] Google search discovery failed: {e}\n")
        
        # Layer 5: Vertical-Specific Discovery
        try:
            print("[LAYER 5] Vertical-Specific Discovery...")
            verticals = ['FinTech', 'BioTech', 'AI', 'ClimateTech', 'Enterprise SaaS']
            vertical_results = await self.discover_from_vertical_specific(verticals)
            all_vcs.extend(vertical_results)
            print(f"[SUCCESS] Vertical-Specific: {len(vertical_results)} investment vehicles\n")
        except Exception as e:
            print(f"[ERROR] Vertical-specific discovery failed: {e}\n")
        
        # Layer 6: Regional Discovery
        try:
            print("[LAYER 6] Regional Directory Discovery...")
            regional_results = await self.discover_from_regional_directories()
            all_vcs.extend(regional_results)
            print(f"[SUCCESS] Regional: {len(regional_results)} investment vehicles\n")
        except Exception as e:
            print(f"[ERROR] Regional discovery failed: {e}\n")
        
        # Layer 7: Known lists (fallback)
        if len(all_vcs) < 50:
            print("[LAYER 4] Known Lists Fallback...")
            known_vcs = [
                {'firm_name': 'Sequoia Capital', 'url': 'https://www.sequoiacap.com/', 'domain': 'sequoiacap.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Andreessen Horowitz', 'url': 'https://a16z.com/', 'domain': 'a16z.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Accel', 'url': 'https://www.accel.com/', 'domain': 'accel.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Greylock Partners', 'url': 'https://www.greylock.com/', 'domain': 'greylock.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Index Ventures', 'url': 'https://www.indexventures.com/', 'domain': 'indexventures.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'General Catalyst', 'url': 'https://www.generalcatalyst.com/', 'domain': 'generalcatalyst.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Insight Partners', 'url': 'https://www.insightpartners.com/', 'domain': 'insightpartners.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Bessemer Venture Partners', 'url': 'https://www.bvp.com/', 'domain': 'bvp.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'GV (Google Ventures)', 'url': 'https://www.gv.com/', 'domain': 'gv.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Khosla Ventures', 'url': 'https://www.khoslaventures.com/', 'domain': 'khoslaventures.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'NEA', 'url': 'https://www.nea.com/', 'domain': 'nea.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Redpoint Ventures', 'url': 'https://www.redpoint.com/', 'domain': 'redpoint.com', 'discovered_from': 'known_list', 'type': 'VC'},
                {'firm_name': 'Y Combinator', 'url': 'https://www.ycombinator.com/', 'domain': 'ycombinator.com', 'discovered_from': 'known_list', 'type': 'Accelerator'},
                {'firm_name': 'Techstars', 'url': 'https://www.techstars.com/', 'domain': 'techstars.com', 'discovered_from': 'known_list', 'type': 'Accelerator'},
                {'firm_name': '500 Global', 'url': 'https://500.co/', 'domain': '500.co', 'discovered_from': 'known_list', 'type': 'Accelerator'},
                {'firm_name': 'Atomic', 'url': 'https://atomic.vc/', 'domain': 'atomic.vc', 'discovered_from': 'known_list', 'type': 'Studio'},
                {'firm_name': 'eFounders', 'url': 'https://www.efounders.com/', 'domain': 'efounders.com', 'discovered_from': 'known_list', 'type': 'Studio'},
            ]
            seen_names = {vc.get('firm_name', '').lower() for vc in all_vcs}
            added_known = 0
            for vc in known_vcs:
                if vc['firm_name'].lower() not in seen_names:
                    all_vcs.append(vc)
                    seen_names.add(vc['firm_name'].lower())
                    added_known += 1
            print(f"[SUCCESS] Known Lists: Added {added_known} from fallback\n")
        
        # Categorize each VC (with error handling)
        print(f"[CATEGORIZATION] Categorizing {len(all_vcs)} investment vehicles...")
        categorized_vcs = []
        for idx, vc in enumerate(all_vcs):
            try:
                categorized = await self.categorize_vc(vc)
                categorized_vcs.append(categorized)
                if (idx + 1) % 50 == 0:
                    print(f"  Categorized {idx + 1}/{len(all_vcs)}...")
            except Exception as e:
                # Add with defaults
                vc.setdefault('stage', 'Unknown')
                vc.setdefault('focus_areas', [])
                vc.setdefault('type', vc.get('type', 'VC'))
                categorized_vcs.append(vc)
        
        print(f"\n{'='*80}")
        print(f"[SUCCESS] Discovery complete: {len(categorized_vcs)} investment vehicles discovered")
        print(f"  - VCs: {sum(1 for v in categorized_vcs if v.get('type') == 'VC')}")
        print(f"  - Accelerators: {sum(1 for v in categorized_vcs if v.get('type') == 'Accelerator')}")
        print(f"  - Studios: {sum(1 for v in categorized_vcs if v.get('type') == 'Studio')}")
        print(f"{'='*80}\n")
        
        return categorized_vcs

