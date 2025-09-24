"""Rate limiting implementation for TinyCode API endpoints"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

class LimitType(Enum):
    """Types of rate limits"""
    PLAN_GENERATION = "plan_generation"
    PLAN_EXECUTION = "plan_execution"
    QUERY = "query"
    FILE_OPERATION = "file_operation"
    RAG_SEARCH = "rag_search"
    API_GENERAL = "api_general"
    # Internet search specific limits
    INTERNET_SEARCH = "internet_search"
    BULK_DOWNLOAD = "bulk_download"
    DOMAIN_REQUESTS = "domain_requests"
    WEB_SCRAPING = "web_scraping"

@dataclass
class RateLimitConfig:
    """Configuration for rate limits"""
    requests_per_minute: int
    burst_size: int
    window_seconds: int = 60

    @classmethod
    def get_defaults(cls) -> Dict[LimitType, 'RateLimitConfig']:
        """Get default rate limit configurations"""
        return {
            LimitType.PLAN_GENERATION: cls(100, 10, 60),      # 100/min, burst 10
            LimitType.PLAN_EXECUTION: cls(50, 5, 60),         # 50/min, burst 5
            LimitType.QUERY: cls(1000, 100, 60),              # 1000/min, burst 100
            LimitType.FILE_OPERATION: cls(200, 20, 60),       # 200/min, burst 20
            LimitType.RAG_SEARCH: cls(500, 50, 60),           # 500/min, burst 50
            LimitType.API_GENERAL: cls(600, 60, 60),          # 600/min, burst 60
            # Internet search limits (more restrictive)
            LimitType.INTERNET_SEARCH: cls(100, 10, 3600),    # 100/hour, burst 10
            LimitType.BULK_DOWNLOAD: cls(10, 2, 3600),        # 10/hour, burst 2
            LimitType.DOMAIN_REQUESTS: cls(50, 5, 3600),      # 50/hour per domain, burst 5
            LimitType.WEB_SCRAPING: cls(30, 3, 3600),         # 30/hour, burst 3
        }

class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on time elapsed
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens are available"""
        with self.lock:
            if self.tokens >= tokens:
                return 0.0

            needed = tokens - self.tokens
            return needed / self.rate

class RateLimiter:
    """Main rate limiter class"""

    def __init__(self, config: Optional[Dict[LimitType, RateLimitConfig]] = None):
        self.config = config or RateLimitConfig.get_defaults()
        self.buckets: Dict[Tuple[str, LimitType], TokenBucket] = {}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()

        # Statistics
        self.stats = defaultdict(lambda: {
            'requests': 0,
            'rejected': 0,
            'last_request': None
        })

    def _get_bucket(self, client_id: str, limit_type: LimitType) -> TokenBucket:
        """Get or create token bucket for client and limit type"""
        key = (client_id, limit_type)

        with self.lock:
            if key not in self.buckets:
                config = self.config[limit_type]
                rate = config.requests_per_minute / 60.0  # Convert to per second
                self.buckets[key] = TokenBucket(rate, config.burst_size)

            return self.buckets[key]

    def check_limit(self, client_id: str, limit_type: LimitType, tokens: int = 1) -> bool:
        """Check if request is within rate limit"""
        bucket = self._get_bucket(client_id, limit_type)

        # Try to consume tokens
        allowed = bucket.consume(tokens)

        # Update statistics
        stats_key = f"{client_id}:{limit_type.value}"
        self.stats[stats_key]['requests'] += 1
        if not allowed:
            self.stats[stats_key]['rejected'] += 1
        self.stats[stats_key]['last_request'] = datetime.now()

        # Record request in history
        self.request_history[client_id].append({
            'time': datetime.now(),
            'type': limit_type.value,
            'allowed': allowed
        })

        return allowed

    def get_wait_time(self, client_id: str, limit_type: LimitType, tokens: int = 1) -> float:
        """Get time to wait before request can be made"""
        bucket = self._get_bucket(client_id, limit_type)
        return bucket.get_wait_time(tokens)

    def reset_limits(self, client_id: Optional[str] = None):
        """Reset rate limits for a client or all clients"""
        with self.lock:
            if client_id:
                # Reset specific client
                keys_to_remove = [k for k in self.buckets.keys() if k[0] == client_id]
                for key in keys_to_remove:
                    del self.buckets[key]
            else:
                # Reset all
                self.buckets.clear()

    def get_stats(self, client_id: Optional[str] = None) -> Dict:
        """Get rate limiting statistics"""
        if client_id:
            client_stats = {}
            for key, stats in self.stats.items():
                if key.startswith(f"{client_id}:"):
                    client_stats[key] = stats
            return client_stats
        return dict(self.stats)

    def cleanup_old_buckets(self, inactive_minutes: int = 60):
        """Clean up inactive token buckets to free memory"""
        cutoff_time = datetime.now() - timedelta(minutes=inactive_minutes)

        with self.lock:
            keys_to_remove = []
            for key in list(self.buckets.keys()):
                client_id = key[0]
                stats_key = f"{client_id}:{key[1].value}"

                last_request = self.stats.get(stats_key, {}).get('last_request')
                if last_request and last_request < cutoff_time:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.buckets[key]

            return len(keys_to_remove)

def rate_limit(limit_type: LimitType, client_id_func: Optional[Callable] = None):
    """Decorator for rate limiting functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get client ID
            if client_id_func:
                client_id = client_id_func(*args, **kwargs)
            else:
                # Default to first argument or 'default'
                client_id = args[0] if args else 'default'

            # Get or create rate limiter (singleton pattern)
            if not hasattr(wrapper, '_rate_limiter'):
                wrapper._rate_limiter = RateLimiter()

            # Check rate limit
            if not wrapper._rate_limiter.check_limit(str(client_id), limit_type):
                wait_time = wrapper._rate_limiter.get_wait_time(str(client_id), limit_type)
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {limit_type.value}. "
                    f"Please wait {wait_time:.1f} seconds."
                )

            return func(*args, **kwargs)

        return wrapper
    return decorator

class MemoryRateLimiter(RateLimiter):
    """In-memory rate limiter (default)"""
    pass

class RedisRateLimiter(RateLimiter):
    """Redis-backed rate limiter for distributed systems"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 config: Optional[Dict[LimitType, RateLimitConfig]] = None):
        super().__init__(config)
        self.redis_url = redis_url
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
        except ImportError:
            raise ImportError("Redis support requires 'redis' package. Install with: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def check_limit(self, client_id: str, limit_type: LimitType, tokens: int = 1) -> bool:
        """Check rate limit using Redis"""
        config = self.config[limit_type]
        key = f"rate_limit:{client_id}:{limit_type.value}"

        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        now = time.time()
        window_start = now - config.window_seconds

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry
        pipe.expire(key, config.window_seconds + 1)

        results = pipe.execute()
        current_requests = results[1]

        # Check if within limit
        if current_requests < config.requests_per_minute:
            return True
        else:
            # Remove the request we just added
            self.redis_client.zrem(key, str(now))
            return False

# Example usage
if __name__ == "__main__":
    # Create rate limiter
    limiter = RateLimiter()

    # Simulate requests
    client = "test_client"

    for i in range(15):
        try:
            allowed = limiter.check_limit(client, LimitType.PLAN_GENERATION)
            if allowed:
                print(f"Request {i+1}: Allowed")
            else:
                wait = limiter.get_wait_time(client, LimitType.PLAN_GENERATION)
                print(f"Request {i+1}: Denied (wait {wait:.1f}s)")
        except RateLimitExceeded as e:
            print(f"Request {i+1}: {e}")

        time.sleep(0.1)

    # Show stats
    print("\nStatistics:")
    print(limiter.get_stats(client))