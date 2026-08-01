import streamlit as st
st.title('deduplicator.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

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
