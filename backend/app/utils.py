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
            key = (fn.__name__, str(args), str(kwargs))
            if key in cache:
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
