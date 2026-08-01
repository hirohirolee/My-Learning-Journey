import streamlit as st

import logging
from datetime import datetime, timezone

import re
import urllib.parse
from bs4 import BeautifulSoup

from core.plugin_registry import BaseParser, registry
from models import Comment, Post

logger = logging.getLogger(__name__)

class GoogleMapsParser(BaseParser):
    def parse(self, html: str, url: str) -> Post:
        soup = BeautifulSoup(html, "html.parser")
        
        title_tag = soup.find("h1")
        title = ""
        if title_tag and title_tag.text.strip():
            title = title_tag.text.strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.replace(" - Google 地圖", "").replace(" - Google Maps", "").replace("Google 地圖", "").replace("Google Maps", "").strip()
            
        if not title or title in ["Google 地圖", "Google Maps", "Google Maps Place"]:
            m = re.search(r'/place/([^/]+)', url)
            if m:
                title = urllib.parse.unquote(m.group(1).replace('+', ' ')).split('/')[0].strip()
            else:
                title = "Google Maps Place"
        
        rating = None
        rating_span = soup.find("span", {"aria-label": lambda x: isinstance(x, str) and "stars" in x.lower()})
        if rating_span:
            try:
                val = rating_span.get("aria-label")
                if isinstance(val, str):
                    rating = float(val.split()[0])
                elif isinstance(val, list):
                    rating = float(val[0].split()[0])
            except (ValueError, IndexError, TypeError):
                pass
                
        comments: list[Comment] = []
        review_blocks = soup.find_all("div", class_="jJc9Ad")
        
        for idx, block in enumerate(review_blocks):
            author_tag = block.find("div", class_="d4r55")
            author = author_tag.text.strip() if author_tag else f"User_{idx}"
            
            content_tag = block.find("span", class_="wiI7pd")
            content = content_tag.text.strip() if content_tag else ""
            
            review_rating = None
            stars = block.find_all("img", src=lambda x: x and "star" in x)
            if stars:
                review_rating = float(len(stars))
                
            if content:
                comments.append(Comment(
                    id=f"{url}_rev_{idx}",
                    post_id=url,
                    author=author,
                    content=content,
                    created_at=datetime.now(timezone.utc),
                    rating=review_rating
                ))

        post_id = url.split('/')[-1] if '/' in url else "gmaps_place"
        return Post(
            id=post_id,
            forum_name="google_maps",
            url=url,
            title=title,
            author="Google Maps",
            content="Google Maps Place",
            created_at=datetime.now(timezone.utc),
            comments=comments,
            rating=rating
        )

registry.register_parser("google.com", GoogleMapsParser)

SCROLL_SCRIPT = """
new Promise(resolve => {
    let tabAttempts = 0;
    
    const startScrolling = () => {
        let scrolls = 0;
        const interval = setInterval(() => {
            let c = document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf') || document.querySelector('.m6QErb');
            if (c) c.scrollTop = c.scrollHeight;
            scrolls++;
            if (scrolls > 5) {
                clearInterval(interval);
                resolve();
            }
        }, 1000);
    };

    const tryClickTab = () => {
        tabAttempts++;
        if (document.querySelector('.jJc9Ad')) {
            startScrolling();
            return;
        }
        
        const tabs = document.querySelectorAll('button, div[role="tab"], [role="tab"], a');
        let clicked = false;
        for (let t of tabs) {
            if (t.innerText && !t.innerText.includes('撰寫') && !t.innerText.includes('Write') && (t.innerText.includes('評論') || t.innerText.includes('Reviews') || t.innerText.includes('則評論'))) {
                t.click();
                clicked = true;
                break;
            }
        }
        
        if (clicked || tabAttempts >= 10) {
            setTimeout(startScrolling, 1500);
        } else {
            setTimeout(tryClickTab, 500);
        }
    };
    
    tryClickTab();
});
"""
registry.register_interaction_script("google.com", SCROLL_SCRIPT)
