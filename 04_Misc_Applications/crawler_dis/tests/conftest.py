from datetime import datetime

import pytest

from models import Comment, Post


@pytest.fixture
def sample_post():
    return Post(
        id="123",
        forum_name="test",
        url="http://test.com/123",
        title="Test Title",
        author="UserA",
        content="This is a test post.",
        created_at=datetime(2026, 1, 1),
        comments=[
            Comment(
                id="c1",
                post_id="123",
                author="UserB",
                content="First!",
                created_at=datetime(2026, 1, 1, 1),
            ),
            Comment(
                id="c2",
                post_id="123",
                author="UserC",
                content="Second!",
                created_at=datetime(2026, 1, 1, 2),
            ),
        ],
    )
