import streamlit as st
st.title('cleaner.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import re

from models import Post


class Cleaner:
    def clean(self, post: Post) -> Post:
        post.title = self._clean_text(post.title)
        post.content = self._clean_text(post.content)
        for c in post.comments:
            c.content = self._clean_text(c.content)
        return post

    def _clean_text(self, text: str) -> str:
        # Remove null bytes and excessive whitespace
        text = text.replace("\x00", "")
        text = re.sub(r"\s+", " ", text).strip()
        return text
