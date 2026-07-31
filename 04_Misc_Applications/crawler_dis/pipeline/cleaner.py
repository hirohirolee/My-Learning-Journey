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
