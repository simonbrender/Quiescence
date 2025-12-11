"""
Celerio Scout - Real OSINT Data Sources
Implements actual data collection from public APIs and sources
"""
import os
import aiohttp
import re
import asyncio
from typing import Dict, Optional, List
from urllib.parse import urlparse
import praw
from bs4 import BeautifulSoup
from cache import cached
from rate_limiter import check_rate_limit, get_wait_time

# Try to import crawl4ai for advanced web scraping
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

# Initialize Reddit client (will use environment variables)
reddit = None
try:
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID', ''),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
        user_agent='CelerioScout/1.0'
    )
except Exception:
    pass  # Will use fallback if Reddit credentials not available

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
SIMILARWEB_API_KEY = os.getenv('SIMILARWEB_API_KEY', '')
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET', '')

@cached(ttl=86400, key_prefix="github_org")  # Cache for 24 hours
async def fetch_github_org(domain: str) -> Optional[str]:
    """
    Try to find GitHub organization from domain using multiple heuristics
    Returns org name if found, None otherwise
    """
    # Extract domain name (e.g., langdb.ai -> langdb)
    domain_parts = domain.replace('www.', '').split('.')
    if len(domain_parts) >= 2:
        potential_orgs = []
        
        # Strategy 1: Use domain name directly (langdb.ai -> langdb)
        potential_orgs.append(domain_parts[0])
        
        # Strategy 2: Try removing common suffixes (langdb-ai -> langdb)
        base_name = domain_parts[0]
        for suffix in ['-ai', '-io', '-app', '-tech', '-labs', '-inc', '-co']:
            if base_name.endswith(suffix):
                potential_orgs.append(base_name[:-len(suffix)])
        
        # Strategy 3: Try camelCase split (langDB -> lang-db)
        if base_name != base_name.lower():
            # Convert camelCase to kebab-case
            import re
            kebab_case = re.sub(r'([a-z])([A-Z])', r'\1-\2', base_name).lower()
            potential_orgs.append(kebab_case)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_orgs = []
        for org in potential_orgs:
            if org not in seen:
                seen.add(org)
                unique_orgs.append(org)
        
        # Try to verify org exists via GitHub API
        if GITHUB_TOKEN:
            # Check rate limit
            if not check_rate_limit('github'):
                wait_time = get_wait_time('github')
                await asyncio.sleep(wait_time)
            
            headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
            async with aiohttp.ClientSession() as session:
                for org_name in unique_orgs:
                    try:
                        # Check if org exists
                        org_url = f'https://api.github.com/orgs/{org_name}'
                        async with session.get(org_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                return org_name
                    except Exception:
                        continue
        
        # Fallback: return first potential org name even without verification
        # (GitHub API will handle 404 gracefully)
        return unique_orgs[0] if unique_orgs else None
    return None

@cached(ttl=3600, key_prefix="github_stats")  # Cache for 1 hour
async def get_github_stats(org_name: str) -> Dict[str, float]:
    """
    Get GitHub statistics using GitHub API
    Returns: last_commit_days, issue_velocity, github_stars
    """
    if not GITHUB_TOKEN:
        return {
            'last_commit_days': 30,
            'issue_velocity': 7,
            'github_stars': 0,
            'repo_count': 0
        }
    
    # Check rate limit
    if not check_rate_limit('github'):
        wait_time = get_wait_time('github')
        await asyncio.sleep(wait_time)
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Get organization repos
            repos_url = f'https://api.github.com/orgs/{org_name}/repos?per_page=10&sort=updated'
            async with session.get(repos_url, headers=headers) as response:
                if response.status == 200:
                    repos = await response.json()
                    if not repos:
                        return {
                            'last_commit_days': 999,
                            'issue_velocity': 999,
                            'github_stars': 0,
                            'repo_count': 0
                        }
                    
                    # Calculate stats from repos
                    total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
                    
                    # Get most recent commit
                    most_recent_commit = None
                    for repo in repos[:5]:  # Check top 5 repos
                        commits_url = f"{repo['url']}/commits?per_page=1"
                        async with session.get(commits_url, headers=headers) as commit_resp:
                            if commit_resp.status == 200:
                                commits = await commit_resp.json()
                                if commits:
                                    commit_date = commits[0]['commit']['author']['date']
                                    if not most_recent_commit or commit_date > most_recent_commit:
                                        most_recent_commit = commit_date
                    
                    # Calculate days since last commit
                    if most_recent_commit:
                        from datetime import datetime
                        commit_dt = datetime.fromisoformat(most_recent_commit.replace('Z', '+00:00'))
                        days_ago = (datetime.now(commit_dt.tzinfo) - commit_dt).days
                    else:
                        days_ago = 999
                    
                    return {
                        'last_commit_days': days_ago,
                        'issue_velocity': 7,  # Would need to calculate from issues
                        'github_stars': total_stars,
                        'repo_count': len(repos)
                    }
        except Exception as e:
            print(f"GitHub API error: {e}")
    
    return {
        'last_commit_days': 999,
        'issue_velocity': 999,
        'github_stars': 0,
        'repo_count': 0
    }

@cached(ttl=7200, key_prefix="reddit_mentions")  # Cache for 2 hours
async def get_reddit_mentions(company_name: str, domain: str) -> Dict[str, float]:
    """
    Search Reddit for company mentions using PRAW
    Returns: reddit_mentions, sentiment_score
    """
    if not reddit:
        # Fallback: return mock data
        return {
            'reddit_mentions': 0,
            'sentiment_score': 50.0
        }
    
    # Check rate limit
    if not check_rate_limit('reddit'):
        wait_time = get_wait_time('reddit')
        await asyncio.sleep(wait_time)
    
    try:
        subreddits = ['SaaS', 'startups', 'artificial', 'entrepreneur']
        total_mentions = 0
        positive_keywords = ['great', 'love', 'amazing', 'excellent', 'good', 'recommend']
        negative_keywords = ['bad', 'hate', 'terrible', 'awful', 'disappointed', 'avoid']
        
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                # Search for company name
                for submission in subreddit.search(company_name, limit=10, sort='relevance'):
                    total_mentions += 1
                    # Check comments too
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:10]:
                        if company_name.lower() in comment.body.lower():
                            total_mentions += 0.5
            except Exception:
                continue
        
        # Simple sentiment scoring
        sentiment_score = 50.0
        if total_mentions > 0:
            sentiment_score = min(80, 50 + (total_mentions * 2))
        
        return {
            'reddit_mentions': int(total_mentions),
            'sentiment_score': sentiment_score
        }
    except Exception as e:
        print(f"Reddit API error: {e}")
        return {
            'reddit_mentions': 0,
            'sentiment_score': 50.0
        }

@cached(ttl=3600, key_prefix="careers")  # Cache for 1 hour (hiring pages change frequently)
async def scrape_careers_page(domain: str) -> Dict[str, Optional[str]]:
    """
    Scrape /careers page to detect hiring activity
    Returns: hiring_status, sales_to_eng_ratio
    """
    async with aiohttp.ClientSession() as session:
        careers_urls = [
            f"https://{domain}/careers",
            f"https://{domain}/jobs",
            f"https://www.{domain}/careers",
            f"https://www.{domain}/jobs"
        ]
        
        for url in careers_urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Look for job listings
                        job_keywords = ['engineer', 'developer', 'sales', 'account executive', 'sdr', 'bdr']
                        job_text = soup.get_text().lower()
                        
                        # Count different types of roles
                        eng_count = sum(1 for kw in ['engineer', 'developer', 'software'] if kw in job_text)
                        sales_count = sum(1 for kw in ['sales', 'account executive', 'sdr', 'bdr', 'account manager'] if kw in job_text)
                        
                        if eng_count == 0 and sales_count == 0:
                            return {
                                'hiring_status': 'unknown',
                                'sales_to_eng_ratio': 1.0
                            }
                        
                        # Calculate ratio
                        if eng_count == 0:
                            ratio = 999 if sales_count > 0 else 1.0
                        else:
                            ratio = sales_count / eng_count if eng_count > 0 else 1.0
                        
                        return {
                            'hiring_status': 'active' if (eng_count + sales_count) > 0 else 'frozen',
                            'sales_to_eng_ratio': ratio
                        }
            except Exception:
                continue
        
        return {
            'hiring_status': 'unknown',
            'sales_to_eng_ratio': 1.0
        }

async def scrape_yc_batch(batch: str) -> List[Dict]:
    """
    Scrape Y Combinator batch page for company list
    Returns list of company dicts with name and domain
    Uses crawl4ai with shorter timeout, falls back to HTTP
    """
    url = f"https://www.ycombinator.com/companies?batch={batch}"
    companies = []
    
    # Try crawl4ai first for JavaScript-heavy pages (with shorter timeout)
    if CRAWL4AI_AVAILABLE:
        try:
            browser_config = BrowserConfig(headless=True, verbose=False)
            crawler_config = CrawlerRunConfig(
                wait_for_images=False,
                process_iframes=False,
                screenshot=False,
                wait_for="domcontentloaded",  # Faster than networkidle
                page_timeout=30000  # 30 seconds
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawler_config)
                
                if result.success and result.html:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # YC website structure - find company cards/links
                    company_links = soup.find_all('a', href=re.compile(r'/companies/'))
                    
                    # NO LIMIT - scrape ALL companies
                    for link in company_links:
                        company_name = link.get_text().strip()
                        if not company_name or len(company_name) < 2:
                            continue
                        
                        # Try to extract domain from href or nearby elements
                        href = link.get('href', '')
                        domain = None
                        
                        # Look for domain in parent/sibling elements
                        parent = link.parent
                        if parent:
                            # Check for domain in text or data attributes
                            text = parent.get_text()
                            domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:com|io|ai|co|dev|app))', text)
                            if domain_match:
                                domain = domain_match.group(1)
                        
                        # Fallback: construct domain from company name
                        if not domain:
                            domain = company_name.lower().replace(' ', '').replace('-', '') + '.com'
                        
                        companies.append({
                            'name': company_name,
                            'domain': domain,
                            'yc_batch': batch,
                            'source': 'yc',
                            'focus_areas': []  # Will be enriched later
                        })
            
            if companies:
                return companies
        except Exception as e:
            print(f"YC crawl4ai scraping error: {e}")
    
    # Fallback to regular HTTP request with proper headers
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    content = await response.text(encoding='utf-8', errors='ignore')
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # YC website structure - find company links
                    company_links = soup.find_all('a', href=re.compile(r'/companies/'))
                    
                    # NO LIMIT - scrape ALL companies
                    for link in company_links:
                        company_name = link.get_text().strip()
                        if company_name and len(company_name) > 2:
                            # Try to extract domain from link or nearby text
                            href = link.get('href', '')
                            domain = None
                            
                            # Look for domain in nearby elements
                            parent = link.parent
                            if parent:
                                text = parent.get_text()
                                domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:com|io|ai|co|dev|app))', text)
                                if domain_match:
                                    domain = domain_match.group(1)
                            
                            # Fallback: construct domain from company name
                            if not domain:
                                domain = company_name.lower().replace(' ', '').replace('-', '') + '.com'
                            
                            companies.append({
                                'name': company_name,
                                'domain': domain,
                                'yc_batch': batch,
                                'source': 'yc',
                                'focus_areas': []
                            })
        except Exception as e:
            print(f"YC HTTP scraping error: {e}")
    
    return companies

@cached(ttl=86400, key_prefix="similarweb")  # Cache for 24 hours (traffic data changes slowly)
async def get_similarweb_data(domain: str) -> Dict[str, float]:
    """
    Get traffic data from SimilarWeb API
    Returns: traffic_score, global_rank, monthly_visits
    """
    if not SIMILARWEB_API_KEY:
        return None
    
    # Check rate limit
    if not check_rate_limit('similarweb'):
        wait_time = get_wait_time('similarweb')
        await asyncio.sleep(wait_time)
    
    async with aiohttp.ClientSession() as session:
        try:
            # SimilarWeb API endpoint (example - adjust based on actual API)
            url = f"https://api.similarweb.com/v1/website/{domain}/total-traffic-and-engagement/visits"
            headers = {
                'Authorization': f'Bearer {SIMILARWEB_API_KEY}',
                'Accept': 'application/json'
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract traffic metrics
                    monthly_visits = data.get('visits', 0)
                    global_rank = data.get('global_rank', 1000000)
                    
                    # Calculate traffic score (0-100)
                    # Higher visits = higher score, but logarithmic scale
                    if monthly_visits > 1000000:
                        traffic_score = 90
                    elif monthly_visits > 100000:
                        traffic_score = 75
                    elif monthly_visits > 10000:
                        traffic_score = 60
                    elif monthly_visits > 1000:
                        traffic_score = 45
                    else:
                        traffic_score = 30
                    
                    return {
                        'traffic_score': traffic_score,
                        'global_rank': global_rank,
                        'monthly_visits': monthly_visits
                    }
        except Exception as e:
            print(f"SimilarWeb API error: {e}")
    
    return None

@cached(ttl=86400, key_prefix="wayback")  # Cache for 24 hours (historical data doesn't change)
async def get_wayback_machine_snapshots(domain: str) -> Dict[str, float]:
    """
    Get historical snapshots from Wayback Machine (archive.org)
    Returns: h1_volatility, snapshot_count, first_seen_date
    """
    # Check rate limit
    if not check_rate_limit('wayback'):
        wait_time = get_wait_time('wayback')
        await asyncio.sleep(wait_time)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Wayback Machine CDX API (no key required, but rate limited)
            url = f"http://web.archive.org/cdx/search/cdx"
            params = {
                'url': domain,
                'output': 'json',
                'limit': 100,
                'filter': 'statuscode:200'
            }
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if len(data) > 1:  # First row is headers
                        snapshot_count = len(data) - 1
                        
                        # Extract H1 tags from recent snapshots to check volatility
                        h1_texts = []
                        for row in data[1:6]:  # Check last 5 snapshots
                            timestamp = row[1]
                            snapshot_url = f"http://web.archive.org/web/{timestamp}/{domain}"
                            
                            try:
                                async with session.get(snapshot_url, timeout=aiohttp.ClientTimeout(total=5)) as snap_resp:
                                    if snap_resp.status == 200:
                                        content = await snap_resp.text()
                                        soup = BeautifulSoup(content, 'html.parser')
                                        h1_tag = soup.find('h1')
                                        if h1_tag:
                                            h1_texts.append(h1_tag.get_text().strip().lower())
                            except Exception:
                                continue
                        
                        # Calculate H1 volatility (how many unique H1s)
                        unique_h1s = len(set(h1_texts)) if h1_texts else 0
                        h1_volatility = unique_h1s - 1 if unique_h1s > 0 else 0
                        
                        # First seen date
                        first_timestamp = data[1][1] if len(data) > 1 else None
                        first_seen_date = None
                        if first_timestamp:
                            from datetime import datetime
                            try:
                                first_seen_date = datetime.strptime(first_timestamp[:8], '%Y%m%d').isoformat()
                            except Exception:
                                pass
                        
                        return {
                            'h1_volatility': h1_volatility,
                            'snapshot_count': snapshot_count,
                            'first_seen_date': first_seen_date
                        }
        except Exception as e:
            print(f"Wayback Machine API error: {e}")
    
    return {
        'h1_volatility': 0,
        'snapshot_count': 0,
        'first_seen_date': None
    }

async def get_linkedin_company_data(company_name: str, domain: str) -> Dict[str, Optional[str]]:
    """
    Get LinkedIn company data using LinkedIn API
    Returns: employee_count, industry, follower_count, recent_posts_count
    Note: Requires OAuth2 setup - see README for details
    """
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        return {
            'employee_count': None,
            'industry': None,
            'follower_count': None,
            'recent_posts_count': None
        }
    
    # LinkedIn API requires OAuth2 token - this is a placeholder structure
    # In production, you'd need to implement OAuth2 flow to get access token
    async with aiohttp.ClientSession() as session:
        try:
            # Search for company by name/domain
            # Note: This requires proper OAuth2 implementation
            # For MVP, we'll return None and use fallbacks
            
            # Example API call structure (requires access token):
            # url = "https://api.linkedin.com/v2/organizationalEntityFollowerStatistics"
            # headers = {
            #     'Authorization': f'Bearer {access_token}',
            #     'X-Restli-Protocol-Version': '2.0.0'
            # }
            
            # For now, return None to use fallbacks
            return {
                'employee_count': None,
                'industry': None,
                'follower_count': None,
                'recent_posts_count': None
            }
        except Exception as e:
            print(f"LinkedIn API error: {e}")
    
    return {
        'employee_count': None,
        'industry': None,
        'follower_count': None,
        'recent_posts_count': None
    }

async def fetch_homepage_with_crawl4ai(url: str) -> Optional[str]:
    """
    Fetch homepage content using crawl4ai for JavaScript-heavy sites
    Falls back to None if crawl4ai is not available
    """
    if not CRAWL4AI_AVAILABLE:
        return None
    
    try:
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        crawler_config = CrawlerRunConfig(
            wait_for_images=False,
            process_iframes=False,
            screenshot=False,
            wait_for="networkidle"  # Wait for JS to load
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if result.success and result.html:
                return result.html
    except Exception as e:
        print(f"Crawl4AI error fetching {url}: {e}")
    
    return None

async def get_traffic_estimate(domain: str) -> Dict[str, float]:
    """
    Get traffic estimate using SimilarWeb API (if available) or heuristics
    """
    # Try SimilarWeb API first
    similarweb_data = await get_similarweb_data(domain)
    if similarweb_data:
        return {
            'traffic_score': similarweb_data['traffic_score'],
            'global_rank': similarweb_data['global_rank'],
            'monthly_visits': similarweb_data.get('monthly_visits', 0)
        }
    
    # Fallback to heuristics
    traffic_score = 50.0
    global_rank = 1000000
    
    # Heuristic scoring based on domain characteristics
    domain_lower = domain.lower()
    
    # Common SaaS patterns
    if any(x in domain_lower for x in ['.io', '.ai', '.app']):
        traffic_score += 10
    
    # Short domains tend to have more traffic
    if len(domain.replace('.', '')) < 10:
        traffic_score += 5
    
    return {
        'traffic_score': min(100, max(0, traffic_score)),
        'global_rank': global_rank,
        'monthly_visits': 0
    }

