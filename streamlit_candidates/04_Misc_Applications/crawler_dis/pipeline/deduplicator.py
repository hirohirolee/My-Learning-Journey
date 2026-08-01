import streamlit as st

import hashlib

from models import Post


class Deduplicator:
    def __init__(self) -> None:
        self._seen_hashes: set[str] = set()

    def is_duplicate(self, post: Post) -> bool:
        # Use URL or ID as unique identifier
        unique_str = f"{post.forum_name}:{post.id}"
        h = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()

        if h in self._seen_hashes:
            return True

        self._seen_hashes.add(h)
        return False
