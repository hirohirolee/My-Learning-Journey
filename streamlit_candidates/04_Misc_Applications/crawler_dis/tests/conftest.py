import streamlit as st
st.title('conftest.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

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


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 sample_post"):
        try:
            res = sample_post() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
