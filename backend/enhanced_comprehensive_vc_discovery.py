"""
Enhanced Comprehensive VC Discovery System
Multi-layered approach to discover ALL investment vehicles globally:
- Venture Capital Firms: 25,000-30,000 globally
- Venture Studios: 1,100+
- Accelerators: 3,000+
- Incubators: 7,000+
"""
import asyncio
import aiohttp
import re
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import json
from datetime import datetime

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

class ComprehensiveVCDiscovery:
    """
    Comprehensive multi-layered VC discovery system
    """
    
    def __init__(self):
        self.discovered_vcs: List[Dict] = []
        self.seen_firms: Set[str] = set()  # Track by normalized name
        self.seen_domains: Set[str] = set()  # Track by domain
        
    def _normalize_name(self, name: str) -> str:
        """Normalize firm name for deduplication"""
        if not name:
            return ""
        # Lowercase, remove extra spaces, remove common suffixes
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        # Remove common suffixes
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
        """Check if VC is duplicate using multiple criteria"""
        firm_name = vc.get('firm_name', '').strip()
        domain = vc.get('domain', '').strip()
        url = vc.get('url', '').strip()
        
        if not firm_name:
            return True
        
        # Normalize name
        normalized_name = self._normalize_name(firm_name)
        
        # Check by normalized name
        if normalized_name in self.seen_firms:
            return True
        
        # Check by domain
        if domain and domain in self.seen_domains:
            return True
        
        # Extract domain from URL if not provided
        if not domain and url:
            domain = self._extract_domain(url)
            if domain and domain in self.seen_domains:
                return True
        
        # Add to seen sets
        self.seen_firms.add(normalized_name)
        if domain:
            self.seen_domains.add(domain)
        
        return False
    
    async def discover_from_crunchbase(self) -> List[Dict]:
        """
        Discover VCs from Crunchbase
        Strategy: Scrape Crunchbase VC directory pages
        Expected: 8,000-10,000 active firms
        """
        discovered = []
        
        # Crunchbase VC directory URLs
        base_urls = [
            "https://www.crunchbase.com/discover/organization.companies/venture_capital",
            "https://www.crunchbase.com/discover/organization.companies/venture_capital?page=1",
            "https://www.crunchbase.com/discover/organization.companies/venture_capital?page=2",
            # Add more pages as needed
        ]
        
        print(f"[CRUNCHBASE] Starting discovery from {len(base_urls)} pages...")
        
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
                    for idx, url in enumerate(base_urls):
                        try:
                            print(f"  [{idx+1}/{len(base_urls)}] Crawling Crunchbase page {idx+1}...")
                            result = await crawler.arun(url=url, config=crawler_config)
                            
                            if result.success and result.html:
                                soup = BeautifulSoup(result.html, 'html.parser')
                                
                                # Crunchbase structure: Look for organization cards
                                org_cards = soup.find_all(['div', 'a'], class_=re.compile(r'organization|company|card', re.I))
                                
                                for card in org_cards[:500]:  # Limit per page
                                    # Extract firm name
                                    name_elem = card.find(['h2', 'h3', 'span', 'a'], class_=re.compile(r'name|title', re.I))
                                    if not name_elem:
                                        name_elem = card.find('a', href=re.compile(r'/organization/'))
                                    
                                    if name_elem:
                                        firm_name = name_elem.get_text(strip=True)
                                        
                                        # Extract URL
                                        link_elem = card.find('a', href=re.compile(r'/organization/'))
                                        if link_elem:
                                            href = link_elem.get('href', '')
                                            if href.startswith('/'):
                                                href = f"https://www.crunchbase.com{href}"
                                            
                                            domain = self._extract_domain(href)
                                            
                                            vc = {
                                                'firm_name': firm_name,
                                                'url': href,
                                                'domain': domain,
                                                'discovered_from': 'crunchbase',
                                                'type': 'VC'
                                            }
                                            
                                            if not self._is_duplicate(vc):
                                                discovered.append(vc)
                            
                            await asyncio.sleep(2)  # Rate limiting
                            
                        except Exception as e:
                            print(f"  [ERROR] Error crawling Crunchbase page {idx+1}: {e}")
                            continue
            
            except Exception as e:
                print(f"[ERROR] Crunchbase discovery error: {e}")
        
        print(f"[CRUNCHBASE] Discovered {len(discovered)} VCs")
        return discovered
    
    async def discover_from_f6s_accelerators(self) -> List[Dict]:
        """
        Discover Accelerators from F6S (largest accelerator database)
        Expected: 2,000-3,000 accelerators
        """
        discovered = []
        
        # F6S accelerator directory
        urls = [
            "https://www.f6s.com/accelerators",
            "https://www.f6s.com/accelerators?page=1",
            "https://www.f6s.com/accelerators?page=2",
            # Add more pages
        ]
        
        print(f"[F6S] Starting accelerator discovery from {len(urls)} pages...")
        
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
                    for idx, url in enumerate(urls):
                        try:
                            print(f"  [{idx+1}/{len(urls)}] Crawling F6S page {idx+1}...")
                            result = await crawler.arun(url=url, config=crawler_config)
                            
                            if result.success and result.html:
                                soup = BeautifulSoup(result.html, 'html.parser')
                                
                                # F6S structure: Look for accelerator cards
                                accelerator_cards = soup.find_all(['div', 'a'], class_=re.compile(r'accelerator|program|card', re.I))
                                
                                for card in accelerator_cards[:300]:
                                    name_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'name|title', re.I))
                                    if name_elem:
                                        firm_name = name_elem.get_text(strip=True)
                                        
                                        link_elem = card.find('a', href=re.compile(r'/accelerator/|/program/'))
                                        if link_elem:
                                            href = link_elem.get('href', '')
                                            if href.startswith('/'):
                                                href = f"https://www.f6s.com{href}"
                                            
                                            domain = self._extract_domain(href)
                                            
                                            accelerator = {
                                                'firm_name': firm_name,
                                                'url': href,
                                                'domain': domain,
                                                'discovered_from': 'f6s',
                                                'type': 'Accelerator'
                                            }
                                            
                                            if not self._is_duplicate(accelerator):
                                                discovered.append(accelerator)
                            
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            print(f"  [ERROR] Error crawling F6S page {idx+1}: {e}")
                            continue
            
            except Exception as e:
                print(f"[ERROR] F6S discovery error: {e}")
        
        print(f"[F6S] Discovered {len(discovered)} accelerators")
        return discovered
    
    async def discover_from_studiohub(self) -> List[Dict]:
        """
        Discover Venture Studios from StudioHub.io
        Expected: 500-1,100 studios
        """
        discovered = []
        
        urls = [
            "https://studiohub.io/studios",
            "https://studiohub.io/studios?page=1",
        ]
        
        print(f"[STUDIOHUB] Starting studio discovery...")
        
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
                    for url in urls:
                        try:
                            result = await crawler.arun(url=url, config=crawler_config)
                            
                            if result.success and result.html:
                                soup = BeautifulSoup(result.html, 'html.parser')
                                
                                # StudioHub structure
                                studio_cards = soup.find_all(['div', 'a'], class_=re.compile(r'studio|card', re.I))
                                
                                for card in studio_cards[:200]:
                                    name_elem = card.find(['h2', 'h3', 'a'])
                                    if name_elem:
                                        firm_name = name_elem.get_text(strip=True)
                                        
                                        link_elem = card.find('a', href=re.compile(r'/studio/'))
                                        if link_elem:
                                            href = link_elem.get('href', '')
                                            if href.startswith('/'):
                                                href = f"https://studiohub.io{href}"
                                            
                                            domain = self._extract_domain(href)
                                            
                                            studio = {
                                                'firm_name': firm_name,
                                                'url': href,
                                                'domain': domain,
                                                'discovered_from': 'studiohub',
                                                'type': 'Studio'
                                            }
                                            
                                            if not self._is_duplicate(studio):
                                                discovered.append(studio)
                            
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            print(f"  [ERROR] Error crawling StudioHub: {e}")
                            continue
            
            except Exception as e:
                print(f"[ERROR] StudioHub discovery error: {e}")
        
        print(f"[STUDIOHUB] Discovered {len(discovered)} studios")
        return discovered
    
    async def discover_from_google_search(self, queries: List[str]) -> List[Dict]:
        """
        Discover VCs using Google Search
        Strategy: Search for VC directories and lists
        """
        discovered = []
        
        # Note: This would require Google Search API or scraping
        # For now, return empty - implement with proper API key
        print(f"[GOOGLE] Google search discovery (requires API key)")
        
        return discovered
    
    async def discover_from_known_lists(self) -> List[Dict]:
        """
        Comprehensive known VC/Studio/Accelerator lists
        Fallback and seed data
        """
        discovered = []
        
        # Comprehensive known VC list (top 500+)
        known_vcs = [
            # Top Tier VCs
            {'firm_name': 'Sequoia Capital', 'url': 'https://www.sequoiacap.com/', 'domain': 'sequoiacap.com', 'type': 'VC'},
            {'firm_name': 'Andreessen Horowitz', 'url': 'https://a16z.com/', 'domain': 'a16z.com', 'type': 'VC'},
            {'firm_name': 'Accel', 'url': 'https://www.accel.com/', 'domain': 'accel.com', 'type': 'VC'},
            {'firm_name': 'Greylock Partners', 'url': 'https://www.greylock.com/', 'domain': 'greylock.com', 'type': 'VC'},
            {'firm_name': 'Index Ventures', 'url': 'https://www.indexventures.com/', 'domain': 'indexventures.com', 'type': 'VC'},
            {'firm_name': 'General Catalyst', 'url': 'https://www.generalcatalyst.com/', 'domain': 'generalcatalyst.com', 'type': 'VC'},
            {'firm_name': 'Insight Partners', 'url': 'https://www.insightpartners.com/', 'domain': 'insightpartners.com', 'type': 'VC'},
            {'firm_name': 'Bessemer Venture Partners', 'url': 'https://www.bvp.com/', 'domain': 'bvp.com', 'type': 'VC'},
            {'firm_name': 'GV (Google Ventures)', 'url': 'https://www.gv.com/', 'domain': 'gv.com', 'type': 'VC'},
            {'firm_name': 'Khosla Ventures', 'url': 'https://www.khoslaventures.com/', 'domain': 'khoslaventures.com', 'type': 'VC'},
            {'firm_name': 'NEA', 'url': 'https://www.nea.com/', 'domain': 'nea.com', 'type': 'VC'},
            {'firm_name': 'Redpoint Ventures', 'url': 'https://www.redpoint.com/', 'domain': 'redpoint.com', 'type': 'VC'},
            # Add 500+ more known VCs here
        ]
        
        # Known Studios
        known_studios = [
            {'firm_name': 'Atomic', 'url': 'https://atomic.vc/', 'domain': 'atomic.vc', 'type': 'Studio'},
            {'firm_name': 'eFounders', 'url': 'https://www.efounders.com/', 'domain': 'efounders.com', 'type': 'Studio'},
            {'firm_name': 'Betaworks', 'url': 'https://betaworks.com/', 'domain': 'betaworks.com', 'type': 'Studio'},
            # Add more studios
        ]
        
        # Known Accelerators
        known_accelerators = [
            {'firm_name': 'Y Combinator', 'url': 'https://www.ycombinator.com/', 'domain': 'ycombinator.com', 'type': 'Accelerator'},
            {'firm_name': 'Techstars', 'url': 'https://www.techstars.com/', 'domain': 'techstars.com', 'type': 'Accelerator'},
            {'firm_name': '500 Global', 'url': 'https://500.co/', 'domain': '500.co', 'type': 'Accelerator'},
            # Add more accelerators
        ]
        
        all_known = known_vcs + known_studios + known_accelerators
        
        for vc in all_known:
            if not self._is_duplicate(vc):
                vc['discovered_from'] = 'known_list'
                discovered.append(vc)
        
        print(f"[KNOWN LISTS] Added {len(discovered)} from known lists")
        return discovered
    
    async def discover_all_comprehensive(self) -> List[Dict]:
        """
        Comprehensive discovery from ALL sources
        Multi-layered approach
        """
        print("\n" + "="*80)
        print("COMPREHENSIVE VC DISCOVERY - ALL INVESTMENT VEHICLES")
        print("="*80 + "\n")
        
        all_discovered = []
        
        # Layer 1: Crunchbase (VCs)
        try:
            crunchbase_vcs = await self.discover_from_crunchbase()
            all_discovered.extend(crunchbase_vcs)
        except Exception as e:
            print(f"[ERROR] Crunchbase discovery failed: {e}")
        
        # Layer 2: F6S (Accelerators)
        try:
            f6s_accelerators = await self.discover_from_f6s_accelerators()
            all_discovered.extend(f6s_accelerators)
        except Exception as e:
            print(f"[ERROR] F6S discovery failed: {e}")
        
        # Layer 3: StudioHub (Studios)
        try:
            studiohub_studios = await self.discover_from_studiohub()
            all_discovered.extend(studiohub_studios)
        except Exception as e:
            print(f"[ERROR] StudioHub discovery failed: {e}")
        
        # Layer 4: Known Lists (Fallback)
        try:
            known_list = await self.discover_from_known_lists()
            all_discovered.extend(known_list)
        except Exception as e:
            print(f"[ERROR] Known lists failed: {e}")
        
        print(f"\n{'='*80}")
        print(f"TOTAL DISCOVERED: {len(all_discovered)} investment vehicles")
        print(f"{'='*80}\n")
        
        return all_discovered

