import streamlit as st
st.title('parser.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import logging

from core.plugin_registry import registry
from exceptions import ParsingException
from models import Post

logger = logging.getLogger(__name__)


class ParserPipeline:
    def parse(self, html: str, url: str, domain: str) -> Post:
        parser_cls = registry.get_parser(domain)
        if not parser_cls:
            available = list(registry._parsers.keys())
            raise ParsingException(f"No parser registered for domain {domain}. Available: {available}")

        parser = parser_cls()
        try:
            post = parser.parse(html, url)
            return post
        except Exception as e:
            raise ParsingException(f"Failed to parse URL {url}: {e}")
