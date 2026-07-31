import asyncio
import logging
from urllib.parse import urlparse

from config import config
from core.cache import LRUCache
from core.engine import PlaywrightEngine
from core.plugin_registry import registry
from exceptions import NetworkException, TimeoutException

logger = logging.getLogger(__name__)


class Fetcher:
    def __init__(self) -> None:
        self.engine = PlaywrightEngine()
        self.cache = (
            LRUCache(config.cache.max_size, config.cache.ttl_sec)
            if config.features.ENABLE_CACHE
            else None
        )

    async def fetch(self, url: str) -> str:
        if self.cache:
            cached = self.cache.get(url)
            if cached:
                logger.info(f"Cache hit for {url}")
                return cached

        attempt = 0
        while attempt < config.retry.max_attempts:
            try:
                domain = urlparse(url).netloc.replace("www.", "")
                js_script = registry.get_interaction_script(domain)
                content = await self.engine.fetch(url, js_script)
                if self.cache:
                    self.cache.set(url, content)
                return content
            except (NetworkException, TimeoutException) as e:
                attempt += 1
                logger.warning(
                    f"Attempt {attempt} failed for {url}: {e}", extra={"retry": attempt}
                )
                if attempt >= config.retry.max_attempts:
                    raise
                await asyncio.sleep(
                    config.retry.backoff_base_sec * (2 ** (attempt - 1))
                )

        raise NetworkException(
            f"Failed to fetch {url} after {config.retry.max_attempts} attempts."
        )

    async def close(self) -> None:
        await self.engine.close()
