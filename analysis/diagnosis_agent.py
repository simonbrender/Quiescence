"""
Celerio Scout - Revenue Architect Diagnosis Agent
Uses LangChain/LangGraph to perform 3M (Market, Motion, Messaging) diagnosis
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not installed. Install with: pip install langchain openai")


class RevenueArchitectAgent:
    """
    Diagnosis agent that analyzes companies using the Celerio 3M Framework
    """
    
    SYSTEM_PROMPT = """You are a Principal Revenue Architect at Celerio, specializing in diagnosing growth stalls in B2B AI startups using the 3M Framework (Market, Motion, Messaging).

Your task is to analyze companies and identify which vector(s) are causing growth stagnation.

THE 3M FRAMEWORK:

1. MARKET VECTOR - Product-Market Fit Issues
   - PMF Drift: Generic website copy, lack of clear positioning
   - Market Saturation: Competing against incumbents without differentiation
   - Bad Revenue: Acquiring customers who don't derive enough value
   Signals: High churn, long sales cycles, low win rates, generic messaging

2. MOTION VECTOR - Go-to-Market Execution Issues
   - MQL Illusion: High lead volume but low SQL conversion
   - Pipeline Velocity: Low win rate or extended sales cycles
   - Brute Force: High SDR count but low traffic/conversion
   - RevOps Failure: Siloed data, manual processes, no single source of truth
   Signals: High activity but low close rate, SDR/AE ratio imbalance, tech stack churn

3. MESSAGING VECTOR - Strategic Narrative Issues
   - Feature Selling: Selling capabilities instead of outcomes
   - No Strategic Narrative: Missing "The Shift" story (Old Game vs New Game)
   - Jargon Density: Technical language that doesn't resonate with buyers
   - Translation Gap: Product works, market exists, but customer doesn't understand value
   Signals: "Nice to have" feedback, low demo-to-close rate, inconsistent messaging

DIAGNOSIS OUTPUT FORMAT:
For each company, provide:
1. Primary Diagnosis: Which vector(s) are failing (Market/Motion/Messaging)
2. Specific Failure Mode: e.g., "MQL Illusion", "PMF Drift", "Feature Selling"
3. Evidence: Specific signals that support the diagnosis
4. Prescription: 90-Day "Scale Without Weight" plan with specific actions

PRESCRIPTION FRAMEWORK:
- Market Failure → Fractional Product Strategist + ICP pivot + pricing model adjustment
- Motion Failure → Fractional Revenue Architect (CRO) + RevOps audit + Digital Twin implementation
- Messaging Failure → Fractional CMO + Strategic Narrative workshop + website overhaul
"""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm and LANGCHAIN_AVAILABLE
        if self.use_llm:
            # Initialize LLM (would need OpenAI API key)
            self.llm = None  # Would initialize here with OpenAI()
    
    def diagnose_company(self, company: Dict) -> Dict:
        """
        Diagnose a single company using 3M framework
        """
        stall_signals = company.get('stall_signals', [])
        
        # Analyze signals to determine vector failures
        market_signals = []
        motion_signals = []
        messaging_signals = []
        
        for signal in stall_signals:
            diagnosis = signal.get('diagnosis', '')
            
            # Categorize by vector
            if diagnosis in ['PMF_Drift', 'Market_Saturation', 'Bad_Revenue']:
                market_signals.append(signal)
            elif diagnosis in ['Motion_Failure', 'Capital_Conservation', 'MQL_Illusion', 'Pipeline_Velocity']:
                motion_signals.append(signal)
            elif diagnosis in ['Feature_Selling', 'No_Strategic_Narrative', 'Jargon_Density']:
                messaging_signals.append(signal)
            elif diagnosis == 'Valley_of_Death_Risk':
                # Can indicate any vector failure
                motion_signals.append(signal)  # Most common
        
        # Determine primary diagnosis
        primary_vector = self._determine_primary_vector(market_signals, motion_signals, messaging_signals)
        
        # Generate diagnosis report
        diagnosis_report = {
            'company_name': company.get('name', 'Unknown'),
            'domain': company.get('domain', ''),
            'primary_diagnosis': primary_vector,
            'vectors': {
                'market': {
                    'status': 'healthy' if not market_signals else 'failing',
                    'signals': market_signals,
                    'failure_mode': self._identify_failure_mode(market_signals, 'market')
                },
                'motion': {
                    'status': 'healthy' if not motion_signals else 'failing',
                    'signals': motion_signals,
                    'failure_mode': self._identify_failure_mode(motion_signals, 'motion')
                },
                'messaging': {
                    'status': 'healthy' if not messaging_signals else 'failing',
                    'signals': messaging_signals,
                    'failure_mode': self._identify_failure_mode(messaging_signals, 'messaging')
                }
            },
            'prescription': self._generate_prescription(primary_vector, market_signals, motion_signals, messaging_signals)
        }
        
        return diagnosis_report
    
    def _determine_primary_vector(self, market: List, motion: List, messaging: List) -> str:
        """Determine which vector is the primary failure"""
        counts = {
            'market': len([s for s in market if s.get('severity') == 'high']),
            'motion': len([s for s in motion if s.get('severity') == 'high']),
            'messaging': len([s for s in messaging if s.get('severity') == 'high'])
        }
        
        if not any(counts.values()):
            return 'healthy'
        
        max_vector = max(counts.items(), key=lambda x: x[1])
        if max_vector[1] > 0:
            return max_vector[0]
        
        # Fallback to medium severity
        medium_counts = {
            'market': len([s for s in market if s.get('severity') == 'medium']),
            'motion': len([s for s in motion if s.get('severity') == 'medium']),
            'messaging': len([s for s in messaging if s.get('severity') == 'medium'])
        }
        
        if any(medium_counts.values()):
            return max(medium_counts.items(), key=lambda x: x[1])[0]
        
        return 'healthy'
    
    def _identify_failure_mode(self, signals: List[Dict], vector: str) -> Optional[str]:
        """Identify specific failure mode from signals"""
        if not signals:
            return None
        
        # Get highest severity signal
        high_severity = [s for s in signals if s.get('severity') == 'high']
        if high_severity:
            return high_severity[0].get('diagnosis')
        
        return signals[0].get('diagnosis')
    
    def _generate_prescription(self, primary_vector: str, market: List, motion: List, messaging: List) -> Dict:
        """Generate 90-Day Scale Without Weight prescription"""
        if primary_vector == 'healthy':
            return {
                'status': 'No intervention needed',
                'recommendation': 'Company appears healthy. Monitor for early warning signals.'
            }
        
        prescription = {
            'primary_vector': primary_vector,
            '90_day_plan': [],
            'fractional_executive': None,
            'key_actions': []
        }
        
        if primary_vector == 'market':
            prescription['fractional_executive'] = 'Fractional Product Strategist'
            prescription['90_day_plan'] = [
                'Week 1-2: PMF Survey & Cohort Analysis - Segment by acquisition cohort, identify "Anti-Personas"',
                'Week 3-4: ICP Matrix Workshop - Define Segment Attractiveness vs Competitive Strength',
                'Week 5-6: Pricing Model Audit - Evaluate unit economics, consider consumption-based pricing',
                'Week 7-8: Segment Pivot Test - Run hypothesis-driven experiments on new ICP segments',
                'Week 9-10: Value Progression Framework - Track Attention → Time → Reputation → Commitment',
                'Week 11-12: PMF Re-validation - Re-run Sean Ellis survey, target >40% "Very Disappointed"'
            ]
            prescription['key_actions'] = [
                'Exclude "Bad Revenue" segments from GTM plan',
                'Adjust pricing model if CAC payback >18 months',
                'Validate new segments before scaling marketing spend'
            ]
        
        elif primary_vector == 'motion':
            prescription['fractional_executive'] = 'Fractional Revenue Architect (CRO)'
            prescription['90_day_plan'] = [
                'Week 1-2: Revenue Architecture Audit - Map Bowtie Model, identify leaky buckets',
                'Week 3-4: RevOps Digital Twin Setup - Automate Sales Velocity reporting, flag rotting deals',
                'Week 5-6: Sales Process Redesign - Implement SPICED framework, fix MQL→SQL handoff',
                'Week 7-8: Pipeline Velocity Optimization - Reduce cycle length, improve win rate',
                'Week 9-10: SDR/AE Ratio Calibration - Right-size outbound capacity',
                'Week 11-12: Tech Stack Optimization - Eliminate shelfware, restore critical tools if needed'
            ]
            prescription['key_actions'] = [
                'Deploy RevOps Digital Twin for automated reporting',
                'Implement "No Demo Without Discovery" gate',
                'Create "Trust Packet" to reduce legal/procurement bottlenecks'
            ]
        
        elif primary_vector == 'messaging':
            prescription['fractional_executive'] = 'Fractional CMO / Strategic Narrative Lead'
            prescription['90_day_plan'] = [
                'Week 1-2: Strategic Narrative Workshop - Apply Andy Raskin framework (The Shift, Stakes, New Game)',
                'Week 3-4: Messaging Audit - NLP analysis of sales calls, identify lexicon gap',
                'Week 5-6: Website Overhaul - Rewrite homepage, deck, remove jargon',
                'Week 7-8: Value Prop Testing - A/B test "Outcome" vs "Feature" messaging',
                'Week 9-10: Sales Enablement - Train team on SPICED framework',
                'Week 11-12: Messaging Validation - Measure demo-to-close rate improvement'
            ]
            prescription['key_actions'] = [
                'Rewrite core pitch using "Old Game vs New Game" framework',
                'Replace feature-focused messaging with outcome-focused',
                'Address "Trust Deficit" with Constitutional AI positioning'
            ]
        
        return prescription
    
    def diagnose_batch(self, companies: List[Dict], filter_criteria: Optional[Dict] = None) -> List[Dict]:
        """
        Diagnose a batch of companies, optionally filtered by criteria
        
        Filter criteria example:
        {
            'funding_range': (3000000, 15000000),
            'headcount_range': (10, 80),
            'months_post_raise': (12, 18),
            'stage': 'Series A'
        }
        """
        # Apply filters if provided
        filtered = companies
        if filter_criteria:
            filtered = self._filter_companies(companies, filter_criteria)
        
        diagnoses = []
        for company in filtered:
            diagnosis = self.diagnose_company(company)
            diagnoses.append(diagnosis)
        
        return diagnoses
    
    def _filter_companies(self, companies: List[Dict], criteria: Dict) -> List[Dict]:
        """Filter companies by criteria"""
        filtered = []
        
        for company in companies:
            # Funding range
            if 'funding_range' in criteria:
                funding = company.get('total_funding', 0)
                min_fund, max_fund = criteria['funding_range']
                if not (min_fund <= funding <= max_fund):
                    continue
            
            # Headcount range
            if 'headcount_range' in criteria:
                headcount = company.get('headcount', 0) or (
                    company.get('engineering_count', 0) + company.get('sales_count', 0)
                )
                min_hc, max_hc = criteria['headcount_range']
                if not (min_hc <= headcount <= max_hc):
                    continue
            
            # Months post-raise
            if 'months_post_raise' in criteria:
                last_funding = company.get('last_funding_date')
                if last_funding:
                    try:
                        funding_date = datetime.fromisoformat(last_funding.replace('Z', '+00:00'))
                        months = (datetime.now() - funding_date.replace(tzinfo=None)).days / 30
                        min_months, max_months = criteria['months_post_raise']
                        if not (min_months <= months <= max_months):
                            continue
                    except:
                        continue
            
            # Stage
            if 'stage' in criteria:
                company_stage = company.get('stage', '').lower()
                if criteria['stage'].lower() not in company_stage:
                    continue
            
            filtered.append(company)
        
        return filtered


def load_enriched_companies(file_path: str = "data/enriched_targets.json") -> List[Dict]:
    """Load enriched companies"""
    path = Path(file_path)
    if not path.exists():
        return []
    
    with open(path, 'r') as f:
        return json.load(f)


def save_diagnoses(diagnoses: List[Dict], file_path: str = "data/diagnoses.json"):
    """Save diagnoses to JSON file"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(diagnoses, f, indent=2)
    
    print(f"Saved {len(diagnoses)} diagnoses to {path}")


if __name__ == "__main__":
    # Test diagnosis agent
    agent = RevenueArchitectAgent()
    
    # Mock enriched company
    test_company = {
        'name': 'Stalling AI Startup',
        'domain': 'example.com',
        'total_funding': 8000000,
        'headcount': 45,
        'stage': 'Series A',
        'last_funding_date': '2023-06-01',
        'stall_signals': [
            {
                'type': 'headcount_divergence',
                'severity': 'high',
                'diagnosis': 'Motion_Failure',
                'details': {'reason': 'Engineering flat, sales declined 50%'}
            },
            {
                'type': 'technographic_churn',
                'severity': 'high',
                'diagnosis': 'Capital_Conservation',
                'details': {'reason': 'Dropped 6sense and Segment'}
            },
            {
                'type': '18_month_window',
                'severity': 'high',
                'diagnosis': 'Valley_of_Death_Risk',
                'details': {'reason': '18+ months since Series A'}
            }
        ]
    }
    
    diagnosis = agent.diagnose_company(test_company)
    
    print("\n=== Diagnosis Test Results ===")
    print(f"Company: {diagnosis['company_name']}")
    print(f"Primary Diagnosis: {diagnosis['primary_diagnosis'].upper()}")
    print(f"\nVector Status:")
    for vector, data in diagnosis['vectors'].items():
        print(f"  {vector.upper()}: {data['status']}")
        if data['failure_mode']:
            print(f"    Failure Mode: {data['failure_mode']}")
    
    print(f"\nPrescription:")
    print(f"  Fractional Executive: {diagnosis['prescription']['fractional_executive']}")
    print(f"\n  90-Day Plan:")
    for action in diagnosis['prescription']['90_day_plan'][:3]:
        print(f"    - {action}")

