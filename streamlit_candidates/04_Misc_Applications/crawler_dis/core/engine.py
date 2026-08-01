import streamlit as st
st.title('engine.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import abc
import asyncio
import logging
from typing import Optional, Any

from config import config
from exceptions import NetworkException, TimeoutException

logger = logging.getLogger(__name__)


class BaseEngine(abc.ABC):
    @abc.abstractmethod
    async def fetch(self, url: str, js_script: Optional[str] = None) -> str:
        """Fetch the HTML content of the given URL."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Release resources."""


class PlaywrightEngine(BaseEngine):
    def __init__(self) -> None:
        from playwright.async_api import (
            Browser,
            BrowserContext,
            Playwright,
        )

        self._playwright_instance: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._lock = asyncio.Lock()

    async def _init_browser(self) -> None:
        if self._browser is not None:
            return

        from playwright.async_api import async_playwright

        self._playwright_instance = await async_playwright().start()
        self._browser = await self._playwright_instance.chromium.launch(
            headless=config.browser.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080",
            ],
        )
        
        # Get real browser user agent and strip Headless indicators
        tmp_context = await self._browser.new_context()
        tmp_page = await tmp_context.new_page()
        ua = await tmp_page.evaluate("navigator.userAgent")
        await tmp_context.close()
        real_ua = ua.replace("HeadlessChrome", "Chrome").replace("Headless", "") if ua else config.browser.user_agents[0]
        
        self._context = await self._browser.new_context(
            user_agent=real_ua,
            viewport={'width': 1920, 'height': 1080},
            locale='zh-TW'
        )

    async def fetch(self, url: str, js_script: Optional[str] = None) -> str:
        async with self._lock:
            await self._init_browser()

        if not self._context:
            raise NetworkException("Browser context not initialized")

        page = await self._context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        try:
            response = await page.goto(
                url, timeout=config.browser.timeout_ms, wait_until="domcontentloaded"
            )
            # Wait for SPA / dynamic content (like Google Maps tabs) to render
            await page.wait_for_timeout(4000)

            if response is None or not response.ok:
                raise NetworkException(
                    f"Failed to fetch {url}: {response.status if response else 'No Response'}"
                )
                
            if js_script:
                logger.info(f"Executing interaction script on {url}")
                await page.evaluate(js_script)
                # Wait a bit for potential network idle after script
                await page.wait_for_timeout(2000)

            content = await page.content()
            return content
        except Exception as e:
            if "Timeout" in str(e):
                raise TimeoutException(f"Timeout fetching {url}: {e}")
            raise NetworkException(f"Error fetching {url}: {e}")
        finally:
            await page.close()

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright_instance:
            await self._playwright_instance.stop()


class FallbackEngine(BaseEngine):
    """
    Fallback engine using Selenium as requested by architecture design.
    Imported lazily to avoid overhead if not used.
    """

    def __init__(self) -> None:
        self._driver: Any = None

    def _init_driver(self) -> None:
        if self._driver is None:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            if config.browser.headless:
                options.add_argument("--headless")
            options.add_argument(f"user-agent={config.browser.user_agents[0]}")
            self._driver = webdriver.Chrome(options=options)
            self._driver.set_page_load_timeout(config.browser.timeout_ms / 1000.0)

    async def fetch(self, url: str, js_script: Optional[str] = None) -> str:
        # Run synchronous selenium in a thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_sync, url, js_script)

    def _fetch_sync(self, url: str, js_script: Optional[str] = None) -> str:
        try:
            self._init_driver()
            if self._driver is None:
                raise NetworkException("Selenium driver not initialized")
            self._driver.get(url)
            if js_script:
                self._driver.execute_script(js_script)
                import time
                time.sleep(2)
            return self._driver.page_source
        except Exception as e:
            raise NetworkException(f"Fallback engine failed on {url}: {e}")

    async def close(self) -> None:
        if self._driver:
            self._driver.quit()
