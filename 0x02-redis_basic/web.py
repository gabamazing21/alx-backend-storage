#!/usr/bin/env python3
import requests
import redis
from functools import wraps
from typing import Callable


r = redis.Redis()


def get_page_count(method: Callable):
    """ get page count"""
    @wraps(method)
    def wrapper(url: str) -> str:
        """wrapper method"""
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
        return html_content
    return wrapper


@get_page_count
def get_page(url: str) -> str:
    """ Fetch the html content of a url and return it"""
    response = requests.get(url, timeout=60)
    # raise an exception for htpp errors
    response.raise_for_status()
    return response.content
