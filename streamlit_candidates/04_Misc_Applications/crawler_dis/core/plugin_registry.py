import streamlit as st

import abc
from typing import Dict, Type, Optional

from models import Post


class BaseParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, html: str, url: str) -> Post:
        pass


class BaseClassifier(abc.ABC):
    @abc.abstractmethod
    def classify(self, post: Post) -> str:
        pass


class BaseExporter(abc.ABC):
    @abc.abstractmethod
    def export(self, posts: list[Post], output_dir: str, run_id: str | None = None) -> None:
        pass


class PluginRegistry:
    def __init__(self) -> None:
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self._classifiers: Dict[str, Type[BaseClassifier]] = {}
        self._exporters: Dict[str, Type[BaseExporter]] = {}
        self._scripts: Dict[str, str] = {}

    def register_interaction_script(self, domain: str, script: str) -> None:
        self._scripts[domain] = script

    def register_parser(self, domain: str, parser_class: Type[BaseParser]) -> None:
        self._parsers[domain] = parser_class

    def register_classifier(
        self, name: str, classifier_class: type[BaseClassifier]
    ) -> None:
        self._classifiers[name] = classifier_class

    def register_exporter(
        self, format_name: str, exporter_class: type[BaseExporter]
    ) -> None:
        self._exporters[format_name] = exporter_class

    def get_parser(self, domain: str) -> type[BaseParser] | None:
        return self._parsers.get(domain)

    def get_classifier(self, name: str) -> type[BaseClassifier] | None:
        return self._classifiers.get(name)

    def get_exporter(self, format_name: str) -> Optional[Type[BaseExporter]]:
        return self._exporters.get(format_name)

    def get_interaction_script(self, domain: str) -> Optional[str]:
        return self._scripts.get(domain)


registry = PluginRegistry()
