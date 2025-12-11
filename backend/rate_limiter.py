"""
Celerio Scout - Rate Limiting
Simple token bucket rate limiter for API calls
"""
import time
from typing import Dict, Optional
from collections import defaultdict

class RateLimiter:
    """
    Token bucket rate limiter
    Each API source gets its own bucket
    """
    def __init__(self):
        self._buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'tokens': 0,
            'last_refill': time.time()
        })
    
    def _refill_tokens(self, source: str, max_tokens: int, refill_rate: float):
        """Refill tokens based on time elapsed"""
        bucket = self._buckets[source]
        now = time.time()
        elapsed = now - bucket['last_refill']
        
        # Add tokens based on refill rate
        tokens_to_add = elapsed * refill_rate
        bucket['tokens'] = min(max_tokens, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
    
    def can_make_request(self, source: str, max_tokens: int = 10, refill_rate: float = 1.0) -> bool:
        """
        Check if we can make a request
        Args:
            source: API source identifier (e.g., 'github', 'reddit', 'similarweb')
            max_tokens: Maximum tokens in bucket
            refill_rate: Tokens per second refill rate
        """
        self._refill_tokens(source, max_tokens, refill_rate)
        bucket = self._buckets[source]
        
        if bucket['tokens'] >= 1.0:
            bucket['tokens'] -= 1.0
            return True
        return False
    
    def wait_time(self, source: str, max_tokens: int = 10, refill_rate: float = 1.0) -> float:
        """Get time to wait before next request is allowed"""
        self._refill_tokens(source, max_tokens, refill_rate)
        bucket = self._buckets[source]
        
        if bucket['tokens'] >= 1.0:
            return 0.0
        
        # Calculate time needed to get 1 token
        tokens_needed = 1.0 - bucket['tokens']
        return tokens_needed / refill_rate
    
    def reset(self, source: Optional[str] = None):
        """Reset rate limiter for a source or all sources"""
        if source:
            if source in self._buckets:
                del self._buckets[source]
        else:
            self._buckets.clear()

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limit configurations per API source
RATE_LIMITS = {
    'github': {'max_tokens': 10, 'refill_rate': 0.5},  # 10 requests, refill 0.5/sec = 20 req/min
    'reddit': {'max_tokens': 5, 'refill_rate': 0.1},  # 5 requests, refill 0.1/sec = 6 req/min
    'similarweb': {'max_tokens': 3, 'refill_rate': 0.05},  # 3 requests, refill 0.05/sec = 3 req/min
    'wayback': {'max_tokens': 5, 'refill_rate': 0.2},  # 5 requests, refill 0.2/sec = 12 req/min
    'linkedin': {'max_tokens': 5, 'refill_rate': 0.1},  # 5 requests, refill 0.1/sec = 6 req/min
    'default': {'max_tokens': 10, 'refill_rate': 1.0}  # Default: 10 req/sec
}

def check_rate_limit(source: str) -> bool:
    """Check if request is allowed for source"""
    config = RATE_LIMITS.get(source, RATE_LIMITS['default'])
    return rate_limiter.can_make_request(
        source,
        max_tokens=config['max_tokens'],
        refill_rate=config['refill_rate']
    )

def get_wait_time(source: str) -> float:
    """Get wait time for source"""
    config = RATE_LIMITS.get(source, RATE_LIMITS['default'])
    return rate_limiter.wait_time(
        source,
        max_tokens=config['max_tokens'],
        refill_rate=config['refill_rate']
    )


