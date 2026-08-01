import streamlit as st
st.title('classifier.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

from core.plugin_registry import registry
from models import Post


class ClassifierPipeline:
    def classify(self, post: Post) -> str:
        # Default simple rule-based classification if no plugin provided
        classifier_cls = registry.get_classifier(post.forum_name)
        if classifier_cls:
            return classifier_cls().classify(post)

        # Basic heuristic
        text = post.title + " " + post.content
        if "問題" in text or "請教" in text or "?" in text or "？" in text:
            return "question"
        if "情報" in text or "新聞" in text:
            return "news"
        if "心得" in text or "討論" in text:
            return "discussion"

        return "general"
