#!/usr/bin/env python3
import redis
import uuid
from typing import Union, Optional, Callable
from functools import wraps


def call_history(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input = f'{method.__qualname__}:inputs'
        output = f'{method.__qualname__}:outputs'

        # Store input arguments
        self._redis.rpush(input, str(args))

        output = method(self, *args, **kwargs)

        # Store Out
        self._redis.rpush(output, output)
        return output
    return wrapper


def count_calls(method: Callable) -> Callable:
    """Decorator to count how many times a method is called."""
    @wraps(method)
    @call_history
    def wrapper(self, *args, **kwargs):
        """Increment the call count and call the original method."""
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def replay(method: Callable) -> None:
    r = redis.Redis()
    methodName = method.__qualname__

    count = r.get(methodName)
    count = int(count) if count else 0

    print(f"{methodName} was called {count} times:")

    inputs_key = f"{methodName}:inputs"
    outputs_key = f"{methodName}:outputs"

    inputs = r.lrange(inputs_key, 0, -1)
    outputs = r.lrange(outputs_key, 0, -1)

    for input_byte, output_byte in zip(inputs, outputs):
        input_str = input_byte.decode('utf-8')
        output_str = output_byte.decode('utf-8')
        print(f"{methodName}(*{input_str}) -> {output_str}")


class Cache:
    def __init__(self):
        """ Initialize redis client and clear databas"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(
            self,
            key: str,
            fn: Optional[Callable[[bytes], Union[str, int]]] = None
            ) -> Union[bytes, str, int, None]:
        """Retrieve data and optionally apply a conversion function."""
        data = self._redis.get(key)
        if data is None:
            return None
        return fn(data) if fn else data

    def get_int(self, key: str):
        """ Automatically decode bytes and convert to integer."""
        return self.get(key, lambda b: int(b.decode("utf-8")))

    def get_str(self, key: str):
        """ Automatically decode bytes to UTF-8 string."""
        return self.get(key, lambda b: b.decode("utf-8"))
