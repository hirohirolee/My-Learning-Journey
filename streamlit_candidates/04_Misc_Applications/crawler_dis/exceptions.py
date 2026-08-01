import streamlit as st
st.title('exceptions.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

class ScraperException(Exception):
    """Base exception for all scraper-related errors."""


class NetworkException(ScraperException):
    """Raised when network requests fail."""


class TimeoutException(ScraperException):
    """Raised when a request or operation times out."""


class ParsingException(ScraperException):
    """Raised when HTML/JSON parsing fails."""


class ValidationException(ScraperException):
    """Raised when data fails schema or business logic validation."""


class ExportException(ScraperException):
    """Raised when data export to file or database fails."""


class CaptchaException(ScraperException):
    """Raised when a CAPTCHA is detected. Triggers abort/alert."""


class ShutdownException(ScraperException):
    """Raised when the system is shutting down gracefully."""
