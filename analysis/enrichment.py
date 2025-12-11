"""
Celerio Scout - OSINT Enrichment Module
Enriches company data with stall signals from various OSINT sources
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class StallSignalEnricher:
    """
    Enriches company data with OSINT-derived stall signals
    Mock implementations ready for real API integration
    """
    
    def __init__(self):
        self.signals = []
    
    def enrich_headcount_divergence(self, company: Dict) -> Dict:
        """
        Signal 1: Headcount Divergence
        Logic: If Engineering_Count is flat but Sales_Count has declined >20% in 6 months, flag as Motion_Failure
        
        Mock implementation - would use LinkedIn API/Proxycurl in production
        """
        # Mock LinkedIn data
        engineering_count_current = company.get('engineering_count', 15)
        engineering_count_6mo = company.get('engineering_count_6mo_ago', 15)
        sales_count_current = company.get('sales_count', 8)
        sales_count_6mo = company.get('sales_count_6mo_ago', 12)
        
        engineering_growth = ((engineering_count_current - engineering_count_6mo) / max(engineering_count_6mo, 1)) * 100
        sales_growth = ((sales_count_current - sales_count_6mo) / max(sales_count_6mo, 1)) * 100
        
        signal = {
            'type': 'headcount_divergence',
            'severity': 'none',
            'diagnosis': None,
            'details': {
                'engineering_count': engineering_count_current,
                'engineering_growth_pct': engineering_growth,
                'sales_count': sales_count_current,
                'sales_growth_pct': sales_growth
            }
        }
        
        # Check for Motion Failure pattern
        if abs(engineering_growth) < 5 and sales_growth < -20:
            signal['severity'] = 'high'
            signal['diagnosis'] = 'Motion_Failure'
            signal['details']['reason'] = 'Engineering headcount flat while sales declined >20% - indicates GTM motion breakdown'
        
        return signal
    
    def enrich_technographic_churn(self, company: Dict) -> Dict:
        """
        Signal 2: Technographic Churn
        Logic: If company dropped 6sense, Demandbase, or Segment in the last 3 months, flag as Capital_Conservation
        
        Mock implementation - would use BuiltWith API in production
        """
        # Mock tech stack data
        current_stack = company.get('tech_stack', ['HubSpot', 'Salesforce', 'Segment'])
        previous_stack_3mo = company.get('tech_stack_3mo_ago', ['HubSpot', 'Salesforce', 'Segment', '6sense', 'Demandbase'])
        
        critical_tools = ['6sense', 'Demandbase', 'Segment', 'Clearbit', 'ZoomInfo']
        dropped_tools = set(previous_stack_3mo) - set(current_stack)
        dropped_critical = [tool for tool in dropped_tools if tool in critical_tools]
        
        signal = {
            'type': 'technographic_churn',
            'severity': 'none',
            'diagnosis': None,
            'details': {
                'current_stack': current_stack,
                'dropped_tools': list(dropped_tools),
                'dropped_critical': dropped_critical
            }
        }
        
        if dropped_critical:
            signal['severity'] = 'high'
            signal['diagnosis'] = 'Capital_Conservation'
            signal['details']['reason'] = f'Dropped critical GTM tools ({", ".join(dropped_critical)}) - indicates cost-cutting and loss of faith in GTM ROI'
        
        return signal
    
    def enrich_18_month_window(self, company: Dict) -> Dict:
        """
        Signal 3: The "18-Month Window"
        Logic: If Last_Funding_Date > 18 months ago AND Stage == "Series A", flag as Valley_of_Death_Risk
        """
        last_funding_date_str = company.get('last_funding_date')
        stage = company.get('stage', '').lower()
        total_funding = company.get('total_funding', 0)
        
        signal = {
            'type': '18_month_window',
            'severity': 'none',
            'diagnosis': None,
            'details': {
                'last_funding_date': last_funding_date_str,
                'stage': stage,
                'total_funding': total_funding
            }
        }
        
        if last_funding_date_str:
            try:
                last_funding = datetime.fromisoformat(last_funding_date_str.replace('Z', '+00:00'))
                months_since_funding = (datetime.now() - last_funding.replace(tzinfo=None)).days / 30
                
                signal['details']['months_since_funding'] = round(months_since_funding, 1)
                
                # Check for Valley of Death risk
                if months_since_funding > 18 and 'series a' in stage:
                    signal['severity'] = 'high'
                    signal['diagnosis'] = 'Valley_of_Death_Risk'
                    signal['details']['reason'] = f'{round(months_since_funding)} months since Series A - operating on fumes, likely distressed'
                elif months_since_funding > 12 and 'series a' in stage:
                    signal['severity'] = 'medium'
                    signal['diagnosis'] = 'Approaching_Valley_of_Death'
                    signal['details']['reason'] = f'{round(months_since_funding)} months since Series A - entering critical window'
            except Exception as e:
                signal['details']['error'] = str(e)
        
        return signal
    
    def enrich_website_signals(self, company: Dict) -> Dict:
        """
        Additional signal: Website copy analysis for PMF Drift
        Logic: Generic website copy indicates lack of clear positioning (Market failure)
        """
        website_copy = company.get('website_copy', '')
        h1_tags = company.get('h1_tags', [])
        
        generic_phrases = [
            'leading', 'innovative', 'cutting-edge', 'revolutionary',
            'best-in-class', 'world-class', 'next-generation'
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in website_copy.lower())
        
        signal = {
            'type': 'website_signals',
            'severity': 'none',
            'diagnosis': None,
            'details': {
                'generic_phrase_count': generic_count,
                'h1_tags': h1_tags,
                'copy_length': len(website_copy)
            }
        }
        
        if generic_count > 3:
            signal['severity'] = 'medium'
            signal['diagnosis'] = 'PMF_Drift'
            signal['details']['reason'] = 'High density of generic marketing phrases - indicates unclear positioning'
        
        return signal
    
    def enrich_social_signals(self, company: Dict) -> Dict:
        """
        Additional signal: Social media engagement
        Logic: Lack of recent "love" on social media indicates Market failure
        """
        last_twitter_mention = company.get('last_twitter_mention_date')
        last_linkedin_post = company.get('last_linkedin_post_date')
        github_stars = company.get('github_stars', 0)
        github_last_commit = company.get('github_last_commit_days', 999)
        
        signal = {
            'type': 'social_signals',
            'severity': 'none',
            'diagnosis': None,
            'details': {
                'github_stars': github_stars,
                'github_last_commit_days': github_last_commit,
                'last_twitter_mention': last_twitter_mention,
                'last_linkedin_post': last_linkedin_post
            }
        }
        
        # Check for stagnation signals
        if github_last_commit > 90:
            signal['severity'] = 'medium'
            signal['diagnosis'] = 'Product_Stagnation'
            signal['details']['reason'] = f'No GitHub commits in {github_last_commit} days - product development stalled'
        
        return signal
    
    def enrich_company(self, company: Dict) -> Dict:
        """
        Run all enrichment signals on a company
        Returns enriched company dict with stall_signals array
        """
        enriched = company.copy()
        stall_signals = []
        
        # Run all enrichment functions
        signals = [
            self.enrich_headcount_divergence(company),
            self.enrich_technographic_churn(company),
            self.enrich_18_month_window(company),
            self.enrich_website_signals(company),
            self.enrich_social_signals(company)
        ]
        
        for signal in signals:
            if signal['severity'] != 'none':
                stall_signals.append(signal)
        
        enriched['stall_signals'] = stall_signals
        enriched['stall_risk_score'] = self._calculate_risk_score(stall_signals)
        
        return enriched
    
    def _calculate_risk_score(self, signals: List[Dict]) -> str:
        """Calculate overall risk score from signals"""
        high_count = sum(1 for s in signals if s['severity'] == 'high')
        medium_count = sum(1 for s in signals if s['severity'] == 'medium')
        
        if high_count >= 2:
            return 'high'
        elif high_count >= 1 or medium_count >= 2:
            return 'medium'
        elif medium_count >= 1:
            return 'low'
        else:
            return 'none'
    
    def enrich_batch(self, companies: List[Dict]) -> List[Dict]:
        """Enrich a batch of companies"""
        enriched = []
        for company in companies:
            enriched_company = self.enrich_company(company)
            enriched.append(enriched_company)
        return enriched


def load_companies(file_path: str = "data/scout_targets.json") -> List[Dict]:
    """Load companies from JSON file"""
    path = Path(file_path)
    if not path.exists():
        return []
    
    with open(path, 'r') as f:
        return json.load(f)


def save_enriched_companies(companies: List[Dict], file_path: str = "data/enriched_targets.json"):
    """Save enriched companies to JSON file"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(companies, f, indent=2)
    
    print(f"Saved {len(companies)} enriched companies to {path}")


if __name__ == "__main__":
    # Test enrichment
    enricher = StallSignalEnricher()
    
    # Mock company for testing
    test_company = {
        'name': 'Test AI Startup',
        'engineering_count': 15,
        'engineering_count_6mo_ago': 15,
        'sales_count': 6,
        'sales_count_6mo_ago': 12,
        'tech_stack': ['HubSpot', 'Salesforce'],
        'tech_stack_3mo_ago': ['HubSpot', 'Salesforce', '6sense', 'Segment'],
        'last_funding_date': '2023-06-01',
        'stage': 'Series A',
        'total_funding': 8000000,
        'website_copy': 'We are a leading innovative cutting-edge revolutionary solution',
        'h1_tags': ['Leading AI Platform'],
        'github_stars': 50,
        'github_last_commit_days': 120
    }
    
    enriched = enricher.enrich_company(test_company)
    
    print("\n=== Enrichment Test Results ===")
    print(f"Company: {enriched['name']}")
    print(f"Risk Score: {enriched['stall_risk_score']}")
    print(f"\nStall Signals ({len(enriched['stall_signals'])}):")
    for signal in enriched['stall_signals']:
        print(f"\n  [{signal['severity'].upper()}] {signal['type']}")
        print(f"  Diagnosis: {signal['diagnosis']}")
        if 'reason' in signal['details']:
            print(f"  Reason: {signal['details']['reason']}")





