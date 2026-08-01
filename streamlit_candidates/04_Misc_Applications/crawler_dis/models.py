import streamlit as st
st.title('models.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Comment:
    id: str
    post_id: str
    author: str
    content: str
    created_at: datetime
    floor: int | None = None
    likes: int = 0
    rating: float | None = None


@dataclass
class Post:
    id: str
    forum_name: str
    url: str
    title: str
    author: str
    content: str
    created_at: datetime
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments: list[Comment] = field(default_factory=list)
    views: int = 0
    likes: int = 0
    rating: float | None = None
