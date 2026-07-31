import logging

from exceptions import ValidationException
from models import Post

logger = logging.getLogger(__name__)


class Validator:
    def validate(self, post: Post) -> Post:
        if not post.id:
            raise ValidationException("Post must have an ID")
        if not post.title:
            raise ValidationException("Post must have a title")
        if not post.content:
            raise ValidationException("Post must have content")

        for comment in post.comments:
            if not comment.id or not comment.content:
                raise ValidationException(f"Invalid comment found in post {post.id}")

        return post
