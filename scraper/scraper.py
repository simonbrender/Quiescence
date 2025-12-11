"""
Celerio Scout - Portfolio Scraper
Uses Crawl4AI to scrape VC portfolio pages with infinite scroll support
"""
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("Warning: Crawl4AI not installed. Install with: pip install crawl4ai")

from bs4 import BeautifulSoup


class PortfolioScraper:
    """Scrapes VC portfolio pages and extracts company information"""
    
    def __init__(self, output_file: str = "data/scout_targets.json"):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.companies = []
    
    async def scrape_nfx_portfolio(self) -> List[Dict]:
        """Scrape NFX portfolio page"""
        if not CRAWL4AI_AVAILABLE:
            return self._mock_nfx_companies()
        
        companies = []
        
        try:
            browser_config = BrowserConfig(
                headless=True,
                verbose=False  # Reduce console output to avoid Unicode issues
            )
            
            crawler_config = CrawlerRunConfig(
                wait_for_images=False,
                process_iframes=False,
                screenshot=False
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url="https://www.nfx.com/portfolio",
                    config=crawler_config
                )
                
                if result.success:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # NFX-specific extraction logic
                    # Look for company cards/links
                    company_elements = soup.find_all(['a', 'div'], class_=re.compile(r'company|portfolio|startup', re.I))
                    
                    for elem in company_elements[:50]:  # Limit to 50 for testing
                        company_name = None
                        description = None
                        sector = None
                        linkedin_url = None
                        
                        # Extract company name
                        name_elem = elem.find(['h1', 'h2', 'h3', 'h4', 'span'], class_=re.compile(r'name|title', re.I))
                        if name_elem:
                            company_name = name_elem.get_text(strip=True)
                        elif elem.name == 'a' and elem.get('href'):
                            company_name = elem.get_text(strip=True)
                        
                        # Extract description
                        desc_elem = elem.find(['p', 'div'], class_=re.compile(r'description|desc|about', re.I))
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                        
                        # Extract LinkedIn URL
                        linkedin_link = elem.find('a', href=re.compile(r'linkedin.com', re.I))
                        if linkedin_link:
                            linkedin_url = linkedin_link.get('href')
                        
                        if company_name and len(company_name) > 2:
                            companies.append({
                                'name': company_name,
                                'description': description or '',
                                'sector': sector or '',
                                'founder_linkedin': linkedin_url or '',
                                'source': 'NFX',
                                'source_url': 'https://www.nfx.com/portfolio'
                            })
            
            return companies if companies else self._mock_nfx_companies()
        except Exception as e:
            print(f"Error scraping NFX: {e}. Using mock data.")
            return self._mock_nfx_companies()
    
    async def scrape_yc_companies(self, batches: List[str] = None) -> List[Dict]:
        """Scrape Y Combinator companies by batch"""
        if not CRAWL4AI_AVAILABLE:
            return self._mock_yc_companies()
        
        if batches is None:
            batches = ['W22', 'S22', 'W23', 'S23', 'W24', 'S24']
        
        companies = []
        
        try:
            browser_config = BrowserConfig(headless=True, verbose=False)
            crawler_config = CrawlerRunConfig(wait_for_images=False)
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for batch in batches:
                    url = f"https://www.ycombinator.com/companies?batch={batch}"
                    result = await crawler.arun(url=url, config=crawler_config)
                    
                    if result.success:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        
                        # YC-specific extraction
                        company_links = soup.find_all('a', href=re.compile(r'/companies/'))
                        
                        for link in company_links[:30]:  # Limit per batch
                            company_name = link.get_text(strip=True)
                            if company_name and len(company_name) > 2:
                                companies.append({
                                    'name': company_name,
                                    'description': '',
                                    'sector': '',
                                    'founder_linkedin': '',
                                    'source': 'Y Combinator',
                                    'source_url': url,
                                    'yc_batch': batch
                                })
            
            return companies if companies else self._mock_yc_companies()
        except Exception as e:
            print(f"Error scraping YC: {e}. Using mock data.")
            return self._mock_yc_companies()
    
    async def scrape_generic_portfolio(self, url: str, firm_name: str) -> List[Dict]:
        """Generic scraper for portfolio pages"""
        if not CRAWL4AI_AVAILABLE:
            return []
        
        companies = []
        
        try:
            browser_config = BrowserConfig(
                headless=True,
                verbose=False
            )
            
            crawler_config = CrawlerRunConfig(
                wait_for_images=False,
                process_iframes=False
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawler_config)
                
                if result.success:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Generic extraction - look for common patterns
                    # Company names in links, headings, or data attributes
                    company_elements = soup.find_all(['a', 'div', 'li'], 
                        attrs={'data-company': True, 'data-name': True, 'class': re.compile(r'company|portfolio', re.I)})
                    
                    # Also check for links that might be company pages
                    potential_links = soup.find_all('a', href=re.compile(r'/company|/portfolio|/startup', re.I))
                    
                    seen_names = set()
                    
                    for elem in list(company_elements) + list(potential_links)[:50]:
                        company_name = None
                        
                        # Try multiple extraction methods
                        if elem.get('data-company'):
                            company_name = elem.get('data-company')
                        elif elem.get('data-name'):
                            company_name = elem.get('data-name')
                        elif elem.name == 'a':
                            company_name = elem.get_text(strip=True)
                            # Skip if it's clearly not a company name
                            if len(company_name) < 3 or company_name.lower() in ['learn more', 'view', 'read more']:
                                continue
                        
                        if company_name and company_name not in seen_names:
                            seen_names.add(company_name)
                            companies.append({
                                'name': company_name,
                                'description': '',
                                'sector': '',
                                'founder_linkedin': '',
                                'source': firm_name,
                                'source_url': url
                            })
            
            return companies
        except Exception as e:
            print(f"Error scraping {firm_name}: {e}")
            return []
    
    def _mock_nfx_companies(self) -> List[Dict]:
        """Mock NFX companies for testing when Crawl4AI not available"""
        return [
            {
                'name': 'Example AI Startup',
                'description': 'AI-powered B2B solution',
                'sector': 'Enterprise AI',
                'founder_linkedin': 'https://linkedin.com/in/founder',
                'source': 'NFX',
                'source_url': 'https://www.nfx.com/portfolio'
            }
        ]
    
    def _mock_yc_companies(self) -> List[Dict]:
        """Mock YC companies for testing"""
        return [
            {
                'name': 'YC AI Company',
                'description': '',
                'sector': '',
                'founder_linkedin': '',
                'source': 'Y Combinator',
                'source_url': 'https://www.ycombinator.com/companies',
                'yc_batch': 'W23'
            }
        ]
    
    async def scrape_all_portfolios(self, seed_data_path: str = "data/seed_data.json") -> List[Dict]:
        """Scrape all portfolios from seed data"""
        seed_path = Path(seed_data_path)
        
        if not seed_path.exists():
            print(f"Seed data file not found: {seed_data_path}")
            return []
        
        with open(seed_path, 'r') as f:
            seed_data = json.load(f)
        
        all_companies = []
        
        # Scrape NFX specifically (known structure)
        print("Scraping NFX portfolio...")
        nfx_companies = await self.scrape_nfx_portfolio()
        all_companies.extend(nfx_companies)
        
        # Scrape YC batches
        print("Scraping Y Combinator companies...")
        yc_companies = await self.scrape_yc_companies()
        all_companies.extend(yc_companies)
        
        # Scrape other portfolios generically
        for vc in seed_data.get('vcs', []):
            if vc['firm_name'] in ['NFX', 'Y Combinator']:
                continue  # Already scraped
            
            print(f"Scraping {vc['firm_name']} portfolio...")
            try:
                companies = await self.scrape_generic_portfolio(vc['url'], vc['firm_name'])
                all_companies.extend(companies)
            except Exception as e:
                print(f"Error scraping {vc['firm_name']}: {e}")
                continue
        
        # Deduplicate by company name
        seen = set()
        unique_companies = []
        for company in all_companies:
            name_lower = company['name'].lower().strip()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_companies.append(company)
        
        return unique_companies
    
    def save_companies(self, companies: List[Dict]):
        """Save scraped companies to JSON file"""
        with open(self.output_file, 'w') as f:
            json.dump(companies, f, indent=2)
        print(f"Saved {len(companies)} companies to {self.output_file}")


async def main():
    """Main scraping function"""
    scraper = PortfolioScraper()
    
    print("Starting portfolio scraping...")
    companies = await scraper.scrape_all_portfolios()
    
    print(f"Scraped {len(companies)} companies")
    scraper.save_companies(companies)
    
    return companies


if __name__ == "__main__":
    companies = asyncio.run(main())
    print(f"\nScraping complete. Found {len(companies)} companies.")

