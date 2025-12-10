"""
Celerio Scout - Data Ingestion Module
Scrapes and ingests startup lists from various sources
"""
import json
import os
from typing import List, Dict

def load_mock_data() -> List[Dict]:
    """
    Load mock data for immediate testing
    Returns 5 sample companies demonstrating different failure modes
    """
    return [
        {
            "id": 1,
            "name": "StagnantAI",
            "domain": "stagnantai.io",
            "yc_batch": "W22",
            "source": "yc",
            "messaging_score": 25.0,  # Bad messaging - high jargon, inconsistent
            "motion_score": 45.0,  # Moderate motion issues
            "market_score": 60.0,  # Decent market signals
            "stall_probability": "high",
            "signals": {
                "messaging": {
                    "messaging_score": 25.0,
                    "h1_volatility": 2,
                    "positioning_consistency": 30.0,
                    "jargon_density": 0.12
                },
                "motion": {
                    "motion_score": 45.0,
                    "traffic_score": 40.0,
                    "hiring_status": "frozen",
                    "sales_to_eng_ratio": 0.3
                },
                "market": {
                    "market_score": 60.0,
                    "sentiment_score": 55.0,
                    "reddit_mentions": 3,
                    "github_stars": 150,
                    "last_commit_days": 45
                }
            }
        },
        {
            "id": 2,
            "name": "RocketShip.io",
            "domain": "rocketship.io",
            "yc_batch": "S22",
            "source": "yc",
            "messaging_score": 75.0,  # Good messaging
            "motion_score": 30.0,  # Bad motion - hiring freeze, traffic down
            "market_score": 70.0,  # Good market signals
            "stall_probability": "medium",
            "signals": {
                "messaging": {
                    "messaging_score": 75.0,
                    "h1_volatility": 0,
                    "positioning_consistency": 85.0,
                    "jargon_density": 0.02
                },
                "motion": {
                    "motion_score": 30.0,
                    "traffic_score": 25.0,
                    "hiring_status": "frozen",
                    "sales_to_eng_ratio": 4.5  # Too many sales, not enough product
                },
                "market": {
                    "market_score": 70.0,
                    "sentiment_score": 75.0,
                    "reddit_mentions": 12,
                    "github_stars": 800,
                    "last_commit_days": 5
                }
            }
        },
        {
            "id": 3,
            "name": "TechJargon Inc",
            "domain": "techjargon.ai",
            "yc_batch": "W23",
            "source": "antler",
            "messaging_score": 20.0,  # Very bad messaging - pure jargon
            "motion_score": 55.0,  # Moderate motion
            "market_score": 40.0,  # Weak market signals
            "stall_probability": "high",
            "signals": {
                "messaging": {
                    "messaging_score": 20.0,
                    "h1_volatility": 3,
                    "positioning_consistency": 20.0,
                    "jargon_density": 0.18
                },
                "motion": {
                    "motion_score": 55.0,
                    "traffic_score": 60.0,
                    "hiring_status": "active",
                    "sales_to_eng_ratio": 1.2
                },
                "market": {
                    "market_score": 40.0,
                    "sentiment_score": 35.0,
                    "reddit_mentions": 0,
                    "github_stars": 25,
                    "last_commit_days": 120
                }
            }
        },
        {
            "id": 4,
            "name": "SilentGrowth",
            "domain": "silentgrowth.com",
            "yc_batch": "S23",
            "source": "github",
            "messaging_score": 65.0,  # Decent messaging
            "motion_score": 35.0,  # Bad motion - silent on socials
            "market_score": 25.0,  # Very bad market - no engagement
            "stall_probability": "high",
            "signals": {
                "messaging": {
                    "messaging_score": 65.0,
                    "h1_volatility": 1,
                    "positioning_consistency": 70.0,
                    "jargon_density": 0.04
                },
                "motion": {
                    "motion_score": 35.0,
                    "traffic_score": 30.0,
                    "hiring_status": "unknown",
                    "sales_to_eng_ratio": 0.8
                },
                "market": {
                    "market_score": 25.0,
                    "sentiment_score": 20.0,
                    "reddit_mentions": 0,
                    "github_stars": 5,
                    "last_commit_days": 200
                }
            }
        },
        {
            "id": 5,
            "name": "HealthyScale",
            "domain": "healthyscale.ai",
            "yc_batch": "W22",
            "source": "yc",
            "messaging_score": 85.0,  # Excellent messaging
            "motion_score": 80.0,  # Strong motion
            "market_score": 75.0,  # Good market signals
            "stall_probability": "low",
            "signals": {
                "messaging": {
                    "messaging_score": 85.0,
                    "h1_volatility": 0,
                    "positioning_consistency": 90.0,
                    "jargon_density": 0.01
                },
                "motion": {
                    "motion_score": 80.0,
                    "traffic_score": 85.0,
                    "hiring_status": "active",
                    "sales_to_eng_ratio": 1.5
                },
                "market": {
                    "market_score": 75.0,
                    "sentiment_score": 80.0,
                    "reddit_mentions": 25,
                    "github_stars": 1200,
                    "last_commit_days": 2
                }
            }
        }
    ]

async def scrape_yc_companies(batches: List[str] = None) -> List[Dict]:
    """
    Scrape Y Combinator company list
    Batches: W22, S22, W23, S23 (Series A Crunch cohort)
    """
    from osint_sources import scrape_yc_batch
    
    if not batches:
        batches = ['W22', 'S22', 'W23', 'S23']
    
    all_companies = []
    for batch in batches:
        companies = await scrape_yc_batch(batch)
        all_companies.extend(companies)
    
    return all_companies

async def scrape_antler_portfolio() -> List[Dict]:
    """
    Scrape Antler portfolio page for AI & B2B companies
    """
    # Mock implementation - in production, use crawl4ai
    return []

async def scrape_github_topics(topics: List[str] = None) -> List[Dict]:
    """
    Search GitHub for repositories with specific topics
    Topics: b2b-saas, enterprise-ai
    Created > 1 year ago
    """
    # Mock implementation - in production, use GitHub API
    return []

