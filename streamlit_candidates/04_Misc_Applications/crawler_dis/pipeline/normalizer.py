import streamlit as st

import unicodedata

from models import Post


class Normalizer:
    def normalize(self, post: Post) -> Post:
        post.title = self._normalize_text(post.title)
        post.content = self._normalize_text(post.content)
        for c in post.comments:
            c.content = self._normalize_text(c.content)
        return post

    def _normalize_text(self, text: str) -> str:
        # Convert full-width characters to half-width, etc.
        return unicodedata.normalize("NFKC", text)
