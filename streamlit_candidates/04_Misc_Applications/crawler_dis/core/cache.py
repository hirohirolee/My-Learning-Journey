import streamlit as st
st.title('cache.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import hashlib
import time
from collections import OrderedDict
from typing import Any


class LRUCache:
    """Thread-unsafe simple LRU cache."""

    def __init__(self, capacity: int, ttl_sec: int) -> None:
        self.capacity = capacity
        self.ttl_sec = ttl_sec
        self.cache: OrderedDict = OrderedDict()

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        hkey = self._hash_key(key)
        if hkey not in self.cache:
            return None

        value, timestamp = self.cache[hkey]
        if time.time() - timestamp > self.ttl_sec:
            # Expired
            self.cache.pop(hkey)
            return None

        self.cache.move_to_end(hkey)
        return value

    def set(self, key: str, value: Any) -> None:
        hkey = self._hash_key(key)
        self.cache[hkey] = (value, time.time())
        self.cache.move_to_end(hkey)

        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
