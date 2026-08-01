import streamlit as st

import logging
from datetime import datetime

from bs4 import BeautifulSoup

from core.plugin_registry import BaseParser, registry
from models import Comment, Post

logger = logging.getLogger(__name__)


class PttParser(BaseParser):
    def parse(self, html: str, url: str) -> Post:
        soup = BeautifulSoup(html, "html.parser")

        # Check for 18+ warning
        if "over18" in html:
            logger.warning(f"PTT 18+ warning detected for {url}")

        main_content = soup.find(id="main-content")
        if not main_content:
            raise ValueError("Cannot find main content")

        meta_values = main_content.find_all("span", class_="article-meta-value")
        if len(meta_values) >= 4:
            author = meta_values[0].text
            meta_values[1].text
            title = meta_values[2].text
            date_str = meta_values[3].text
            try:
                # "Sat Jul 25 10:00:00 2026" format
                created_at = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
            except ValueError:
                created_at = datetime.utcnow()
        else:
            author = "Unknown"
            title = "Unknown"
            created_at = datetime.utcnow()

        # Extract text content by removing meta tags and comments
        for meta in main_content.find_all("div", class_="article-metaline"):
            meta.extract()
        for meta in main_content.find_all("div", class_="article-metaline-right"):
            meta.extract()

        pushes = main_content.find_all("div", class_="push")
        comments: list[Comment] = []
        for push in pushes:
            push.extract()
            push_tag = push.find("span", class_="push-tag")
            push_userid = push.find("span", class_="push-userid")
            push_content = push.find("span", class_="push-content")

            if push_tag and push_userid and push_content:
                comment = Comment(
                    id=f"{url}_comment_{len(comments)}",
                    post_id=url,
                    author=push_userid.text.strip(),
                    content=push_content.text.replace(":", "").strip(),
                    created_at=created_at,  # fallback
                )
                comments.append(comment)

        content = main_content.text.strip()

        post_id = url.split("/")[-1].replace(".html", "")

        return Post(
            id=post_id,
            forum_name="ptt",
            url=url,
            title=title,
            author=author,
            content=content,
            created_at=created_at,
            comments=comments,
        )


# Auto register
registry.register_parser("ptt.cc", PttParser)
