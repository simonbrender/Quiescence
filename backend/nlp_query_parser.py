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
                    timeout=5  # Reduced timeout - fail fast and use rule-based parser
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
            except requests.exceptions.Timeout:
                print(f"[OLLAMA] Request timed out (5s), falling back to rule-based parsing")
            except requests.exceptions.RequestException as e:
                print(f"[OLLAMA] Request error: {e}, falling back to rule-based parsing")
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
    parsed = rule_based_parse(query)
    if progress_callback:
        progress_callback({
            'type': 'rule_based_parse_complete',
            'message': 'Rule-based parsing completed',
            'parsed_params': parsed,
            'timestamp': datetime.now().isoformat()
        })
    return parsed


def rule_based_parse(query: str) -> Dict:
    """
    Enhanced fallback rule-based parser for when Ollama is not available.
    Handles complex queries with multiple criteria.
    """
    query_lower = query.lower()
    params = {}
    
    # Extract stages (handle "Seed/Series A" format)
    stages = []
    stage_patterns = {
        'pre-seed': 'Pre-Seed',
        'seed': 'Seed',
        'series a': 'Series A',
        'series b': 'Series B',
        'series c': 'Series C',
        'growth': 'Growth'
    }
    
    # Handle slash-separated stages like "Seed/Series A"
    stage_slash_match = re.search(r'(seed|pre-seed|series\s+[abc]|growth)(?:\s*/\s*(seed|pre-seed|series\s+[abc]|growth))?', query_lower)
    if stage_slash_match:
        for group in stage_slash_match.groups():
            if group:
                # Normalize the stage name
                for pattern, stage in stage_patterns.items():
                    if pattern in group.lower():
                        if stage not in stages:
                            stages.append(stage)
                        break
    
    # Also check for individual stage mentions
    for pattern, stage in stage_patterns.items():
        if pattern in query_lower and stage not in stages:
            stages.append(stage)
    
    if stages:
        params['stages'] = stages
    
    # Extract focus areas (handle "AI/B2B" format)
    focus_areas = []
    focus_patterns = {
        'ai/ml': 'AI/ML',
        'ai': 'AI/ML',
        'machine learning': 'AI/ML',
        'ml': 'AI/ML',
        'b2b': 'B2B SaaS',
        'saas': 'B2B SaaS',
        'fintech': 'Fintech',
        'enterprise': 'Enterprise',
        'devtools': 'DevTools',
        'dev tools': 'DevTools'
    }
    
    # Handle slash-separated focus areas like "AI/B2B"
    focus_slash_match = re.search(r'(ai|ml|b2b|saas|fintech|enterprise|devtools|dev tools)(?:\s*/\s*(ai|ml|b2b|saas|fintech|enterprise|devtools|dev tools))?', query_lower)
    if focus_slash_match:
        for group in focus_slash_match.groups():
            if group:
                for pattern, area in focus_patterns.items():
                    if pattern in group.lower():
                        if area not in focus_areas:
                            focus_areas.append(area)
                        break
    
    # Also check for individual focus area mentions
    # But avoid false positives - require word boundaries
    # Skip "ai" pattern as it matches too many things (like "raise", "paid", etc.)
    for pattern, area in focus_patterns.items():
        if pattern == 'ai':  # Skip standalone "ai" to avoid false positives
            continue
        # Use word boundaries to avoid matching substrings
        pattern_regex = r'\b' + re.escape(pattern) + r'\b'
        if re.search(pattern_regex, query_lower) and area not in focus_areas:
            focus_areas.append(area)
    
    # Only check for "ai" if it appears with context like "AI companies" or "AI/ML"
    if re.search(r'\bai\b.*(?:companies?|startups?|firms?|businesses?|/ml|/machine)', query_lower, re.IGNORECASE):
        if 'AI/ML' not in focus_areas:
            focus_areas.append('AI/ML')
    
    if focus_areas:
        params['focus_areas'] = focus_areas
    
    # Extract months post-raise FIRST (before funding) to avoid conflicts
    # Handle "12–18 months post-raise", "6-12 months ago", "raised 6-12 months ago"
    months_patterns = [
        r'(\d+)\s*[-–—]\s*(\d+)\s+months?\s+post[- ]raise',  # "12-18 months post-raise"
        r'raised\s+(\d+)\s*[-–—]\s*(\d+)\s+months?\s+ago',  # "raised 6-12 months ago"
        r'(\d+)\s*[-–—]\s*(\d+)\s+months?\s+ago',  # "6-12 months ago" (only if not already matched)
    ]
    
    months_found = False
    months_matched_text = ""
    for pattern in months_patterns:
        months_match = re.search(pattern, query_lower)
        if months_match:
            params['months_post_raise_min'] = int(months_match.group(1))
            params['months_post_raise_max'] = int(months_match.group(2))
            months_found = True
            months_matched_text = months_match.group(0)
            break
    
    # Extract funding ranges - improved regex to handle various formats
    # Handle "$3–15m", "$3-15m", "$3 to $15m", "$3-$15m", "3-15 million"
    # Must include $ or "million" or "m" to avoid matching months
    funding_patterns = [
        r'\$(\d+(?:\.\d+)?)\s*[-–—]\s*\$?(\d+(?:\.\d+)?)\s*m(?:illion)?',  # Range: $3-15m (must start with $)
        r'\$?(\d+(?:\.\d+)?)\s*[-–—]\s*\$?(\d+(?:\.\d+)?)\s+m(?:illion)',  # Range: 3-15 million (must have "million")
        r'\$?(\d+(?:\.\d+)?)\s+to\s+\$?(\d+(?:\.\d+)?)\s*m(?:illion)?',  # Range: $3 to $15m
        r'(?:with|having|of|funding)\s+\$?(\d+(?:\.\d+)?)\s*[-–—]\s*\$?(\d+(?:\.\d+)?)\s*m(?:illion)?',  # "with $3-15m"
        r'\$?(\d+(?:\.\d+)?)\s*[-–—]\s*\$?(\d+(?:\.\d+)?)\s*m\s+(?:in\s+)?(?:total\s+)?funding',  # "$3-15m in total funding"
    ]
    
    funding_found = False
    for pattern in funding_patterns:
        funding_match = re.search(pattern, query_lower)
        if funding_match:
            # Make sure we didn't match the months_post_raise text
            matched_text = funding_match.group(0)
            if not months_found or months_matched_text not in matched_text:
                params['funding_min'] = float(funding_match.group(1))
                params['funding_max'] = float(funding_match.group(2))
                funding_found = True
                break
    
    # Handle single funding amounts: "over $50M", "more than $10m", "at least $5M"
    if not funding_found:
        funding_min_patterns = [
            r'(?:over|more than|at least|minimum|min)\s+\$?(\d+(?:\.\d+)?)\s*m(?:illion)?',
            r'\$?(\d+(?:\.\d+)?)\s+m(?:illion)?\s+(?:and\s+)?over',
        ]
        for pattern in funding_min_patterns:
            funding_min_match = re.search(pattern, query_lower)
            if funding_min_match:
                params['funding_min'] = float(funding_min_match.group(1))
                break
        
        funding_max_patterns = [
            r'(?:under|less than|up to|maximum|max)\s+\$?(\d+(?:\.\d+)?)\s*m(?:illion)?',
            r'\$?(\d+(?:\.\d+)?)\s+m(?:illion)?\s+(?:and\s+)?under',
        ]
        for pattern in funding_max_patterns:
            funding_max_match = re.search(pattern, query_lower)
            if funding_max_match:
                params['funding_max'] = float(funding_max_match.group(1))
                break
    
    # Extract employee ranges - improved to handle various formats
    # Handle "10-80 employees", "10 to 80 employees", "with 5-20 employees"
    emp_patterns = [
        r'(\d+)\s*[-–—]\s*(\d+)\s+employees?',  # Range: 10-80 employees
        r'(\d+)\s+to\s+(\d+)\s+employees?',  # Range: 10 to 80 employees
        r'(?:with|having|of)\s+(\d+)\s*[-–—]\s*(\d+)\s+employees?',  # "with 10-80 employees"
    ]
    
    emp_found = False
    for pattern in emp_patterns:
        emp_match = re.search(pattern, query_lower)
        if emp_match:
            params['employees_min'] = int(emp_match.group(1))
            params['employees_max'] = int(emp_match.group(2))
            emp_found = True
            break
    
    # Handle single employee constraints: "less than 10", "over 50", "at least 20"
    if not emp_found:
        emp_min_patterns = [
            r'(?:over|more than|at least|minimum|min)\s+(\d+)\s+employees?',
            r'(\d+)\s+employees?\s+(?:and\s+)?over',
        ]
        for pattern in emp_min_patterns:
            emp_min_match = re.search(pattern, query_lower)
            if emp_min_match:
                params['employees_min'] = int(emp_min_match.group(1))
                break
        
        emp_max_patterns = [
            r'(?:under|less than|up to|maximum|max|fewer than)\s+(\d+)\s+employees?',
            r'(\d+)\s+employees?\s+(?:and\s+)?(?:under|less)',
        ]
        for pattern in emp_max_patterns:
            emp_max_match = re.search(pattern, query_lower)
            if emp_max_match:
                params['employees_max'] = int(emp_max_match.group(1))
                break
    
    # Extract fund tiers - improved to handle "tier 1/2", "tier1/2", "Tier 1 or Tier 2"
    fund_tiers = []
    if re.search(r'tier\s*1[/\s]2|tier1[/\s]2|tier\s*1\s+or\s+tier\s*2', query_lower):
        fund_tiers = ['Tier 1', 'Tier 2']
    else:
        if 'tier 1' in query_lower or 'tier1' in query_lower:
            fund_tiers.append('Tier 1')
        if 'tier 2' in query_lower or 'tier2' in query_lower:
            fund_tiers.append('Tier 2')
    
    if fund_tiers:
        params['fund_tiers'] = fund_tiers
    
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

