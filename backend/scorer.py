"""
Celerio Scout - Triangulation Engine
Calculates Messaging, Motion, and Market vector scores
"""
import asyncio
import aiohttp
import re
from urllib.parse import urlparse
from typing import Dict, Optional
import textstat
import json

async def fetch_url(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Optional[str]:
    """Fetch URL content with timeout"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

async def check_web_traffic(domain: str) -> Dict[str, float]:
    """
    Proxy for web traffic using public signals
    Returns: traffic_score (0-100), global_rank (lower is better)
    """
    from osint_sources import get_traffic_estimate
    
    try:
        return await get_traffic_estimate(domain)
    except Exception as e:
        print(f"Traffic check error: {e}")
        return {
            'traffic_score': 50.0,
            'global_rank': 1000000
        }

async def check_social_signals(company_name: str, domain: str) -> Dict[str, float]:
    """
    Check Reddit mentions and social engagement
    Returns: reddit_mentions, sentiment_score
    """
    from osint_sources import get_reddit_mentions
    
    try:
        return await get_reddit_mentions(company_name, domain)
    except Exception as e:
        print(f"Social signals error: {e}")
        return {
            'reddit_mentions': 0,
            'sentiment_score': 50.0
        }

async def check_engineering_pulse(domain: str, company_name: str = "") -> Dict[str, float]:
    """
    Check GitHub activity and engineering velocity
    Returns: last_commit_days, issue_velocity, github_stars
    """
    from osint_sources import fetch_github_org, get_github_stats
    
    # Try to find GitHub org
    org_name = await fetch_github_org(domain)
    if org_name:
        stats = await get_github_stats(org_name)
        return stats
    
    # Fallback to mock data
    return {
        'last_commit_days': 30,
        'issue_velocity': 7,
        'github_stars': 0
    }

async def check_hiring_signals(domain: str) -> Dict[str, Optional[str]]:
    """
    Check /careers page for hiring activity
    Returns: hiring_status, sales_to_eng_ratio
    """
    from osint_sources import scrape_careers_page
    
    try:
        return await scrape_careers_page(domain)
    except Exception as e:
        print(f"Hiring signals error: {e}")
        return {
            'hiring_status': 'unknown',
            'sales_to_eng_ratio': 1.0
        }

async def analyze_messaging(domain: str, company_name: str) -> Dict[str, float]:
    """
    Analyze messaging vector:
    - H1 volatility (via Wayback Machine)
    - Positioning consistency (title vs LinkedIn)
    - Jargon density
    """
    from osint_sources import get_wayback_machine_snapshots, get_linkedin_company_data, fetch_homepage_with_crawl4ai
    
    async with aiohttp.ClientSession() as session:
        # Try to fetch homepage
        homepage_url = f"https://{domain}" if not domain.startswith('http') else domain
        content = await fetch_url(session, homepage_url)
        
        # If simple HTTP fetch fails, try crawl4ai for JavaScript-heavy sites
        if not content:
            content = await fetch_homepage_with_crawl4ai(homepage_url)
        
        if not content:
            return {
                'messaging_score': 50.0,
                'h1_volatility': 0,
                'positioning_consistency': 50.0,
                'jargon_density': 0.05
            }
        
        # Extract H1 and title
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        
        h1_text = h1_match.group(1).strip() if h1_match else ""
        title_text = title_match.group(1).strip() if title_match else ""
        
        # Calculate jargon density (AI buzzwords)
        ai_buzzwords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 
                       'neural network', 'llm', 'gpt', 'transformer', 'generative']
        all_text = (h1_text + " " + title_text).lower()
        jargon_count = sum(1 for word in ai_buzzwords if word in all_text)
        jargon_density = jargon_count / max(len(all_text.split()), 1)
        
        # Get Wayback Machine data for H1 volatility
        wayback_data = await get_wayback_machine_snapshots(domain)
        h1_volatility = wayback_data.get('h1_volatility', 0)
        
        # Get LinkedIn data for positioning consistency
        linkedin_data = await get_linkedin_company_data(company_name, domain)
        
        # Positioning consistency (check if title and H1 are similar)
        positioning_score = 50.0
        if h1_text and title_text:
            # Simple similarity check
            h1_words = set(h1_text.lower().split())
            title_words = set(title_text.lower().split())
            if h1_words and title_words:
                overlap = len(h1_words & title_words) / len(h1_words | title_words)
                positioning_score = overlap * 100
        
        # If LinkedIn data available, enhance positioning score
        if linkedin_data.get('industry'):
            # Could compare LinkedIn industry with messaging positioning
            positioning_score = min(100, positioning_score + 10)
        
        # Calculate messaging score
        # High score = low jargon, high consistency, low volatility
        messaging_score = (
            (1 - min(jargon_density * 10, 1)) * 40 +  # Jargon penalty (max 40 points)
            positioning_score * 0.4 +  # Consistency (max 40 points)
            (1 - min(h1_volatility / 3, 1)) * 20  # Stability (max 20 points)
        )
        
        return {
            'messaging_score': max(0, min(100, messaging_score)),
            'h1_volatility': h1_volatility,
            'positioning_consistency': positioning_score,
            'jargon_density': jargon_density,
            'wayback_snapshots': wayback_data.get('snapshot_count', 0)
        }

async def analyze_motion(domain: str, company_name: str = "") -> Dict[str, float]:
    """
    Analyze motion vector:
    - Traffic growth
    - Hiring activity
    - Sales velocity proxies
    """
    # Get signals
    traffic_data = await check_web_traffic(domain)
    hiring_data = await check_hiring_signals(domain)
    
    # Calculate motion score
    traffic_score = traffic_data['traffic_score']
    
    # Hiring component
    hiring_score = 50.0
    if hiring_data['hiring_status'] == 'active':
        hiring_score = 70.0
    elif hiring_data['hiring_status'] == 'frozen':
        hiring_score = 20.0
    
    # Sales to Eng ratio component
    ratio_score = 50.0
    ratio = hiring_data.get('sales_to_eng_ratio', 1.0)
    if 0.5 <= ratio <= 2.0:  # Healthy range
        ratio_score = 70.0
    elif ratio > 3.0:  # Too many sales, not enough product
        ratio_score = 30.0
    
    # Motion score = weighted average
    motion_score = (
        traffic_score * 0.4 +
        hiring_score * 0.4 +
        ratio_score * 0.2
    )
    
    return {
        'motion_score': max(0, min(100, motion_score)),
        'traffic_score': traffic_score,
        'hiring_status': hiring_data['hiring_status'],
        'sales_to_eng_ratio': ratio
    }

async def analyze_market(domain: str, company_name: str = "") -> Dict[str, float]:
    """
    Analyze market vector:
    - PMF proxies (technographic churn, social sentiment)
    - Unit economics proxies
    """
    # Get signals
    social_data = await check_social_signals(company_name, domain)
    eng_data = await check_engineering_pulse(domain, company_name)
    
    # Social sentiment component
    sentiment_score = social_data['sentiment_score']
    reddit_mentions = social_data['reddit_mentions']
    
    # GitHub stars component (proxy for product-market fit)
    github_score = 50.0
    if eng_data['github_stars'] > 500:
        github_score = 80.0
    elif eng_data['github_stars'] > 100:
        github_score = 60.0
    elif eng_data['github_stars'] == 0:
        github_score = 30.0
    
    # Activity component (recent commits)
    activity_score = 50.0
    if eng_data['last_commit_days'] < 7:
        activity_score = 80.0
    elif eng_data['last_commit_days'] < 30:
        activity_score = 60.0
    elif eng_data['last_commit_days'] > 90:
        activity_score = 20.0
    
    # Market score = weighted average
    market_score = (
        sentiment_score * 0.3 +
        github_score * 0.4 +
        activity_score * 0.3
    )
    
    return {
        'market_score': max(0, min(100, market_score)),
        'sentiment_score': sentiment_score,
        'reddit_mentions': reddit_mentions,
        'github_stars': eng_data['github_stars'],
        'last_commit_days': eng_data['last_commit_days']
    }

def calculate_stall_probability(messaging_score: float, motion_score: float, market_score: float) -> str:
    """Calculate overall stall probability"""
    avg_score = (messaging_score + motion_score + market_score) / 3
    
    if avg_score < 40:
        return "high"
    elif avg_score < 60:
        return "medium"
    else:
        return "low"

async def calculate_scores(domain: str, company_name: str) -> Dict:
    """
    Main scoring function - runs all analyses in parallel
    Returns complete score dictionary
    """
    # Run all analyses concurrently
    messaging_task = analyze_messaging(domain, company_name)
    motion_task = analyze_motion(domain, company_name)
    market_task = analyze_market(domain, company_name)
    
    messaging_result, motion_result, market_result = await asyncio.gather(
        messaging_task, motion_task, market_task
    )
    
    # Extract scores
    messaging_score = messaging_result['messaging_score']
    motion_score = motion_result['motion_score']
    market_score = market_result['market_score']
    
    # Calculate stall probability
    stall_probability = calculate_stall_probability(messaging_score, motion_score, market_score)
    
    # Combine all signals
    signals = {
        'messaging': messaging_result,
        'motion': motion_result,
        'market': market_result
    }
    
    return {
        'messaging_score': round(messaging_score, 2),
        'motion_score': round(motion_score, 2),
        'market_score': round(market_score, 2),
        'stall_probability': stall_probability,
        'signals': signals
    }

async def scan_company(url: str) -> Dict:
    """
    Scan a single company URL and return complete analysis
    """
    from datetime import datetime
    
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    if not domain:
        domain = url
    
    # Extract company name from domain
    company_name = domain.split('.')[0].title()
    
    # Calculate scores
    scores = await calculate_scores(domain, company_name)
    
    now = datetime.now()
    
    return {
        'id': hash(domain) % 1000000,  # Simple hash-based ID
        'name': company_name,
        'domain': domain,
        'yc_batch': '',  # Empty for scanned companies
        'source': 'scanned',
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        **scores
    }

