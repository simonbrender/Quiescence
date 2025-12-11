"""
Natural Language Query Parser using Ollama
Parses free-text search queries into structured search parameters
"""
import json
import re
from typing import Dict, Optional, List
from datetime import datetime
import requests

OLLAMA_BASE_URL = "http://localhost:11434"

# Try these models in order of preference
OLLAMA_MODELS = ["llama3.2", "mistral", "phi3", "qwen2.5", "llama3.1", "llama2"]

def check_ollama_available():
    # Returns: (is_available: bool, model_name: Optional[str])
    """
    Check if Ollama is available and return the first available model.
    Returns (is_available, model_name)
    """
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            available_model_names = [m.get('name', '') for m in models]
            available_models_short = [m.split(':')[0] for m in available_model_names]
            
            # Find first available model from our preference list
            for preferred_model in OLLAMA_MODELS:
                # Check if model name matches (handles "llama2:latest" format)
                for idx, model_short in enumerate(available_models_short):
                    if preferred_model.lower() in model_short.lower():
                        return True, available_model_names[idx]  # Return full model name
            
            # If no preferred model found, use first available
            if available_model_names:
                return True, available_model_names[0]
            
            return False, None
    except:
        pass
    return False, None

def parse_natural_language_query(query: str, progress_callback=None) -> Dict:
    """
    Parse a natural language query into structured search parameters.
    
    Example queries:
    - "Seed/Series A AI/B2B companies 12–18 months post-raise, typically with $3–15m in total funding from a Tier1/2 fund and 10–80 employees"
    - "Series-B startups experiencing a sudden spike in new hires in their sales team, headquartered on the East Coast US and UAE"
    
    Returns a dictionary with structured search parameters.
    """
    try:
        # Check if Ollama is available
        ollama_available, model_name = check_ollama_available()
        
        if ollama_available and model_name:
            try:
                # Use chat API for better results with structured output
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": """You are a helpful assistant that extracts structured search parameters from natural language queries about companies.
Extract the following information if mentioned:
- stages: List of investment stages (e.g., ["Seed", "Series A", "Series B"])
- focus_areas: List of focus areas (e.g., ["AI/ML", "B2B SaaS", "Fintech"])
- funding_min: Minimum funding in millions USD (e.g., 3)
- funding_max: Maximum funding in millions USD (e.g., 15)
- employees_min: Minimum employee count (e.g., 10)
- employees_max: Maximum employee count (e.g., 80)
- months_post_raise_min: Minimum months since last raise (e.g., 12)
- months_post_raise_max: Maximum months since last raise (e.g., 18)
- fund_tiers: List of fund tiers (e.g., ["Tier 1", "Tier 2"])
- locations: List of locations (e.g., ["East Coast US", "UAE"])
- keywords: List of additional keywords mentioned (e.g., ["sales team", "hiring spike"])

Return ONLY valid JSON, no other text. Use null for missing values."""
                            },
                            {
                                "role": "user",
                                "content": f'Parse this query: "{query}"'
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 500
                        },
                        "format": "json"
                    },
                    timeout=30  # Increased timeout for slower models
                )
            
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('message', {}).get('content', '')
                    
                    # Try to parse as JSON directly
                    try:
                        parsed = json.loads(response_text)
                        print(f"[OLLAMA] Successfully parsed query using Ollama model: {model_name}")
                        print(f"[OLLAMA] Parsed parameters: {json.dumps(parsed, indent=2)}")
                        return normalize_parsed_params(parsed)
                    except json.JSONDecodeError:
                        # Extract JSON from response (handle markdown code blocks)
                        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                        if json_match:
                            parsed = json.loads(json_match.group(0))
                            print(f"[OLLAMA] Successfully parsed query using Ollama model: {model_name}")
                            print(f"[OLLAMA] Parsed parameters: {json.dumps(parsed, indent=2)}")
                            return normalize_parsed_params(parsed)
                        else:
                            print(f"[OLLAMA] Could not extract JSON from Ollama response, falling back to rule-based parsing")
                            print(f"[OLLAMA] Response was: {response_text[:500]}")
            except Exception as e:
                print(f"[OLLAMA] API error: {e}, falling back to rule-based parsing")
                import traceback
                traceback.print_exc()
        else:
            print(f"[OLLAMA] Not available (checked models: {OLLAMA_MODELS}), using rule-based parsing")
            print(f"[OLLAMA] Available: {ollama_available}, Model: {model_name}")
    except Exception as e:
        print(f"[OLLAMA] Error checking Ollama: {e}, falling back to rule-based parsing")
        import traceback
        traceback.print_exc()
    
    # Fallback to rule-based parsing
    return rule_based_parse(query)


def rule_based_parse(query: str) -> Dict:
    """
    Fallback rule-based parser for when Ollama is not available.
    """
    query_lower = query.lower()
    params = {}
    
    # Extract stages
    stages = []
    stage_patterns = {
        'pre-seed': 'Pre-Seed',
        'seed': 'Seed',
        'series a': 'Series A',
        'series b': 'Series B',
        'series c': 'Series C',
        'growth': 'Growth'
    }
    for pattern, stage in stage_patterns.items():
        if pattern in query_lower:
            stages.append(stage)
    if stages:
        params['stages'] = stages
    
    # Extract focus areas
    focus_areas = []
    focus_patterns = {
        'ai/ml': 'AI/ML',
        'ai': 'AI/ML',
        'machine learning': 'AI/ML',
        'b2b': 'B2B SaaS',
        'saas': 'B2B SaaS',
        'fintech': 'Fintech',
        'enterprise': 'Enterprise',
        'devtools': 'DevTools'
    }
    for pattern, area in focus_patterns.items():
        if pattern in query_lower:
            if area not in focus_areas:
                focus_areas.append(area)
    if focus_areas:
        params['focus_areas'] = focus_areas
    
    # Extract funding ranges
    funding_match = re.search(r'\$?(\d+)\s*[-–]?\s*(\d+)\s*m(?:illion)?', query_lower)
    if funding_match:
        params['funding_min'] = float(funding_match.group(1))
        params['funding_max'] = float(funding_match.group(2))
    else:
        funding_min_match = re.search(r'(?:over|more than|at least)\s*\$?(\d+)\s*m', query_lower)
        funding_max_match = re.search(r'(?:under|less than|up to)\s*\$?(\d+)\s*m', query_lower)
        if funding_min_match:
            params['funding_min'] = float(funding_min_match.group(1))
        if funding_max_match:
            params['funding_max'] = float(funding_max_match.group(1))
    
    # Extract employee ranges
    emp_match = re.search(r'(\d+)\s*[-–]?\s*(\d+)\s*employees?', query_lower)
    if emp_match:
        params['employees_min'] = int(emp_match.group(1))
        params['employees_max'] = int(emp_match.group(2))
    
    # Extract months post-raise
    months_match = re.search(r'(\d+)\s*[-–]?\s*(\d+)\s*months?\s*post[- ]raise', query_lower)
    if months_match:
        params['months_post_raise_min'] = int(months_match.group(1))
        params['months_post_raise_max'] = int(months_match.group(2))
    
    # Extract fund tiers
    if 'tier 1' in query_lower or 'tier1' in query_lower:
        params['fund_tiers'] = ['Tier 1']
    if 'tier 2' in query_lower or 'tier2' in query_lower:
        if 'fund_tiers' not in params:
            params['fund_tiers'] = []
        params['fund_tiers'].append('Tier 2')
    
    # Detect portfolio queries
    portfolio_keywords = ['portfolio', 'portfolios', 'retrieve', 'scrape', 'get', 'fetch', 'load', 'import']
    portfolio_sources = []
    if 'yc' in query_lower or 'y combinator' in query_lower or 'ycombinator' in query_lower:
        portfolio_sources.append('yc')
    if 'antler' in query_lower:
        portfolio_sources.append('antler')
    
    # If query mentions portfolios and sources, mark as portfolio query
    if any(keyword in query_lower for keyword in portfolio_keywords) and portfolio_sources:
        params['portfolio_sources'] = portfolio_sources
        params['is_portfolio_query'] = True
    
    # Default rank by stall
    params['rank_by_stall'] = True
    
    return params


def normalize_parsed_params(parsed: Dict) -> Dict:
    """
    Normalize parsed parameters to match expected format.
    """
    normalized = {}
    
    # Normalize stages
    if 'stages' in parsed and parsed['stages']:
        normalized['stages'] = [s.strip() for s in parsed['stages'] if s]
    
    # Normalize focus areas
    if 'focus_areas' in parsed and parsed['focus_areas']:
        normalized['focus_areas'] = [f.strip() for f in parsed['focus_areas'] if f]
    
    # Normalize numeric fields
    for field in ['funding_min', 'funding_max', 'employees_min', 'employees_max', 
                  'months_post_raise_min', 'months_post_raise_max']:
        if field in parsed and parsed[field] is not None:
            try:
                normalized[field] = float(parsed[field]) if 'funding' in field else int(parsed[field])
            except (ValueError, TypeError):
                pass
    
    # Normalize fund tiers
    if 'fund_tiers' in parsed and parsed['fund_tiers']:
        normalized['fund_tiers'] = [t.strip() for t in parsed['fund_tiers'] if t]
    
    # Store locations and keywords for potential future use
    if 'locations' in parsed:
        normalized['locations'] = parsed['locations']
    if 'keywords' in parsed:
        normalized['keywords'] = parsed['keywords']
    
    # Default rank by stall
    normalized['rank_by_stall'] = parsed.get('rank_by_stall', True)
    
    return normalized

