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

async def fetch_github_org(domain: str) -> Optional[str]:
    """
    Try to find GitHub organization from domain
    Returns org name if found, None otherwise
    """
    # Common patterns: github.com/{org}, {org}.github.io
    # For now, try to extract from domain
    domain_parts = domain.replace('www.', '').split('.')
    if len(domain_parts) >= 2:
        # Try the main domain name as GitHub org
        potential_org = domain_parts[0]
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

async def get_traffic_estimate(domain: str) -> Dict[str, float]:
    """
    Get traffic estimate using public APIs or heuristics
    For now, uses heuristics based on domain patterns
    """
    # In production, integrate with SimilarWeb API or other services
    # For MVP, use heuristics
    
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
        'global_rank': global_rank
    }

