from datetime import datetime

import pytest

from exceptions import ValidationException
from models import Post
from pipeline.classifier import ClassifierPipeline
from pipeline.cleaner import Cleaner
from pipeline.deduplicator import Deduplicator
from pipeline.validator import Validator


def test_validator_success(sample_post):
    validator = Validator()
    validated = validator.validate(sample_post)
    assert validated.id == "123"


def test_validator_failure():
    validator = Validator()
    invalid_post = Post(
        id="",
        forum_name="test",
        url="",
        title="",
        author="",
        content="",
        created_at=datetime.utcnow(),
    )
    with pytest.raises(ValidationException):
        validator.validate(invalid_post)


def test_cleaner(sample_post):
    sample_post.title = "Test  \x00 Title"
    cleaner = Cleaner()
    cleaned = cleaner.clean(sample_post)
    assert cleaned.title == "Test Title"


def test_deduplicator(sample_post):
    dedup = Deduplicator()
    assert not dedup.is_duplicate(sample_post)
    assert dedup.is_duplicate(sample_post)  # Second time should be true


def test_classifier(sample_post):
    sample_post.title = "請問這是什麼問題？"
    classifier = ClassifierPipeline()
    category = classifier.classify(sample_post)
    assert category == "question"
