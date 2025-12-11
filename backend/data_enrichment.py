"""
Celerio Scout - Data Enrichment Module
Enriches company data with funding, employee count, and raise information
"""
import re
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import aiohttp
from bs4 import BeautifulSoup

# Tier 1/2 VC funds (well-known, established funds)
TIER_1_2_FUNDS = {
    'Y Combinator', 'Sequoia Capital', 'Andreessen Horowitz', 'a16z', 
    'Benchmark', 'Accel Partners', 'First Round Capital', 'NFX',
    'Lightspeed Venture Partners', 'Founders Fund', 'Craft Ventures',
    'SignalFire', 'Greylock Partners', 'Kleiner Perkins', 'NEA',
    'Bessemer Venture Partners', 'Index Ventures', 'General Catalyst',
    'Insight Partners', 'Tiger Global', 'Coatue', 'IVP'
}

async def extract_funding_info(domain: str, company_name: str) -> Dict:
    """
    Extract funding information from company website or Crunchbase
    Returns: funding_amount (in USD), funding_currency, last_raise_date, last_raise_stage
    """
    # Try to find funding info on company website (about page, press, etc.)
    async with aiohttp.ClientSession() as session:
        urls_to_check = [
            f"https://{domain}/about",
            f"https://{domain}/press",
            f"https://{domain}/news",
            f"https://www.{domain}/about"
        ]
        
        for url in urls_to_check:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text()
                        
                        # Look for funding patterns: "$5M", "$10 million", "raised $15M"
                        funding_patterns = [
                            r'\$(\d+(?:\.\d+)?)\s*(?:million|M|m)',
                            r'raised\s+\$(\d+(?:\.\d+)?)\s*(?:million|M|m)',
                            r'(\d+(?:\.\d+)?)\s*(?:million|M|m)\s*(?:USD|dollar)',
                        ]
                        
                        for pattern in funding_patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            if matches:
                                amount_str = matches[0]
                                try:
                                    amount = float(amount_str)
                                    # Convert to USD if needed (simplified)
                                    return {
                                        'funding_amount': amount * 1000000,  # Convert to dollars
                                        'funding_currency': 'USD',
                                        'last_raise_date': None,  # Would need more sophisticated parsing
                                        'last_raise_stage': None
                                    }
                                except:
                                    continue
            except:
                continue
    
    return {
        'funding_amount': None,
        'funding_currency': None,
        'last_raise_date': None,
        'last_raise_stage': None
    }

async def extract_employee_count(domain: str) -> Optional[int]:
    """
    Extract employee count from company website (about page, team page)
    """
    async with aiohttp.ClientSession() as session:
        urls_to_check = [
            f"https://{domain}/about",
            f"https://{domain}/team",
            f"https://www.{domain}/about"
        ]
        
        for url in urls_to_check:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text()
                        
                        # Look for employee count patterns: "50 employees", "team of 30", "30+ people"
                        patterns = [
                            r'(\d+)\s*(?:employees|people|team members)',
                            r'team\s+of\s+(\d+)',
                            r'(\d+)\+?\s*(?:employees|people)',
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            if matches:
                                try:
                                    count = int(matches[0])
                                    if 1 <= count <= 1000:  # Reasonable range
                                        return count
                                except:
                                    continue
            except:
                continue
    
    return None

def determine_fund_tier(vc_name: str) -> Optional[str]:
    """
    Determine if VC is Tier 1 or Tier 2 based on known list
    """
    vc_name_lower = vc_name.lower()
    for tier_fund in TIER_1_2_FUNDS:
        if tier_fund.lower() in vc_name_lower or vc_name_lower in tier_fund.lower():
            return "Tier 1"
    
    # Could add Tier 2 logic here
    return None

async def enrich_company_data(company: Dict, domain: str) -> Dict:
    """
    Enrich company data with funding, employee count, and other metadata
    """
    # Extract funding info
    funding_info = await extract_funding_info(domain, company.get('name', ''))
    
    # Extract employee count
    employee_count = await extract_employee_count(domain)
    
    # Determine fund tier
    fund_tier = None
    if company.get('source'):
        fund_tier = determine_fund_tier(company['source'])
    
    # Estimate raise date if we have YC batch
    last_raise_date = None
    last_raise_stage = None
    if company.get('yc_batch'):
        # YC batches are roughly: W22 = Feb 2022, S22 = Aug 2022, etc.
        batch = company['yc_batch']
        if batch.startswith('W'):
            year = 2000 + int(batch[1:])
            last_raise_date = datetime(year, 2, 1).date()
            last_raise_stage = "Seed"
        elif batch.startswith('S'):
            year = 2000 + int(batch[1:])
            last_raise_date = datetime(year, 8, 1).date()
            last_raise_stage = "Seed"
    
    return {
        **company,
        **funding_info,
        'employee_count': employee_count,
        'last_raise_date': last_raise_date,
        'last_raise_stage': last_raise_stage,
        'fund_tier': fund_tier
    }


