import re
import html 
from cachetools import TTLCache
from functools import wraps

_cache = TTLCache(maxsize=256, ttl=120)

def simple_cache(ttl_seconds: int = 120):
    cache = TTLCache(maxsize=256, ttl=ttl_seconds)
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # Create a more explicit cache key that includes all relevant parameters
            # Sort kwargs to ensure consistent key generation
            sorted_kwargs = tuple(sorted(kwargs.items())) if kwargs else ()
            key = (fn.__name__, args, sorted_kwargs)
            if key in cache:
                import logging
                logging.info(f"Cache hit for {fn.__name__} with key: {key}")
                return cache[key]
            res = await fn(*args, **kwargs)
            cache[key] = res
            return res
        return wrapper
    return decorator

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
     # remove URLs
    text = re.sub(r'http\S+', '', text)
    # remove newlines and repeated spaces
    text = re.sub(r'\s+', ' ', text).strip()
    # optional: strip non-printables
    text = ''.join(ch for ch in text if ord(ch) >= 32)
    return text
