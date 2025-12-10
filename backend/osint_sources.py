"""
Celerio Scout - Real OSINT Data Sources
Implements actual data collection from public APIs and sources
"""
import os
import aiohttp
import re
from typing import Dict, Optional, List
from urllib.parse import urlparse
import praw
from bs4 import BeautifulSoup

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

async def fetch_github_org(domain: str) -> Optional[str]:
    """
    Try to find GitHub organization from domain
    Returns org name if found, None otherwise
    """
    # Extract domain name (e.g., langdb.ai -> langdb)
    domain_parts = domain.replace('www.', '').split('.')
    if len(domain_parts) >= 2:
        potential_org = domain_parts[0]
        
        # Try to verify org exists via GitHub API
        if GITHUB_TOKEN:
            headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
            async with aiohttp.ClientSession() as session:
                try:
                    # Check if org exists
                    org_url = f'https://api.github.com/orgs/{potential_org}'
                    async with session.get(org_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            return potential_org
                except Exception:
                    pass
        
        # Fallback: return potential org name even without verification
        # (GitHub API will handle 404 gracefully)
        return potential_org
    return None

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
    """
    async with aiohttp.ClientSession() as session:
        url = f"https://www.ycombinator.com/companies?batch={batch}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    companies = []
                    # YC website structure - find company links
                    company_links = soup.find_all('a', href=re.compile(r'/companies/'))
                    
                    for link in company_links[:50]:  # Limit to 50
                        company_name = link.get_text().strip()
                        if company_name:
                            # Try to extract domain from link or nearby text
                            domain = company_name.lower().replace(' ', '') + '.com'  # Fallback
                            companies.append({
                                'name': company_name,
                                'domain': domain,
                                'yc_batch': batch,
                                'source': 'yc'
                            })
                    
                    return companies
        except Exception as e:
            print(f"YC scraping error: {e}")
    
    return []

async def get_similarweb_data(domain: str) -> Dict[str, float]:
    """
    Get traffic data from SimilarWeb API
    Returns: traffic_score, global_rank, monthly_visits
    """
    if not SIMILARWEB_API_KEY:
        return None
    
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

async def get_wayback_machine_snapshots(domain: str) -> Dict[str, float]:
    """
    Get historical snapshots from Wayback Machine (archive.org)
    Returns: h1_volatility, snapshot_count, first_seen_date
    """
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

