import requests
import redis
from functools import wraps


r = redis.Redis()
def get_page_count(method: callable):
    @wraps(method)
    def wrapper(url: str) -> str:
        key = f"count:{url}"
        r.incr(key)
    
        # Check if the content is cached
        cached_key = f"cache:{url}"
        cached_content = r.get(cached_key)
        if cached_content:
            return cached_content.decode('utf-8')
        
        # Fetch the content if not in cache
        html_content = method(url)
        r.setex(cached_key, 10, html_content)

def get_page(url: str) -> str:
    """ Fetch the html content of a url and return it"""
    response = requests.get(url)
    # raise an exception for htpp errors
    response.raise_for_status()
    return response.text