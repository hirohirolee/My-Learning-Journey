import json
import logging
from datetime import datetime

from core.plugin_registry import BaseParser, registry
from models import Comment, Post

logger = logging.getLogger(__name__)


class DcardParser(BaseParser):
    def parse(self, html_or_json: str, url: str) -> Post:
        try:
            data = json.loads(html_or_json)
        except json.JSONDecodeError:
            raise ValueError("DcardParser currently expects JSON from Dcard API")

        post_id = str(data.get("id", ""))
        title = data.get("title", "No Title")
        content = data.get("content", "")
        author = data.get("member", {}).get("alias", "Anonymous")
        forum_name = "dcard"

        date_str = data.get("createdAt")
        try:
            created_at = (
                datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if date_str
                else datetime.utcnow()
            )
        except ValueError:
            created_at = datetime.utcnow()

        comments: list[Comment] = []

        return Post(
            id=post_id,
            forum_name=forum_name,
            url=url,
            title=title,
            author=author,
            content=content,
            created_at=created_at,
            comments=comments,
        )


# Auto register
registry.register_parser("dcard.tw", DcardParser)
