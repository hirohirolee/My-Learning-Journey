import streamlit as st
st.title('test_pipeline.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

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


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 test_validator_success"):
        try:
            res = test_validator_success() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_validator_failure"):
        try:
            res = test_validator_failure() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_cleaner"):
        try:
            res = test_cleaner() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_deduplicator"):
        try:
            res = test_deduplicator() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 test_classifier"):
        try:
            res = test_classifier() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
