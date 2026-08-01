import streamlit as st
st.title('controller.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import asyncio
import logging
import threading
from queue import Empty, Queue
from urllib.parse import urlparse

# Ensure plugins are registered
import plugins.ptt  # noqa: F401
import plugins.dcard  # noqa: F401
import plugins.google_maps  # noqa: F401

from models import Post
from pipeline.classifier import ClassifierPipeline
from pipeline.cleaner import Cleaner
from pipeline.deduplicator import Deduplicator
from pipeline.exporter import ExporterPipeline
from pipeline.fetcher import Fetcher
from pipeline.normalizer import Normalizer
from pipeline.parser import ParserPipeline
from pipeline.validator import Validator

logger = logging.getLogger(__name__)


class CancellationToken:
    """Thread-safe token to signal cancellation and pause across threads and async tasks."""

    def __init__(self) -> None:
        self._is_cancelled: bool = False
        self._is_paused: bool = False
        self._lock = threading.Lock()

    def cancel(self) -> None:
        with self._lock:
            self._is_cancelled = True

    def pause(self) -> None:
        with self._lock:
            self._is_paused = True

    def resume(self) -> None:
        with self._lock:
            self._is_paused = False

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._is_cancelled

    @property
    def is_paused(self) -> bool:
        with self._lock:
            return self._is_paused


class ScraperController:
    """
    Coordinates the execution of the scraping pipeline in a dedicated background thread.
    Ensures that the Streamlit main thread is never blocked by asyncio.run().
    """

    def __init__(self) -> None:
        self.cancellation_token = CancellationToken()
        self._worker_thread: threading.Thread | None = None
        self._async_loop: asyncio.AbstractEventLoop | None = None
        self._metrics_queue: Queue = Queue()
        self._is_running: bool = False

        self.parser = ParserPipeline()
        self.validator = Validator()
        self.cleaner = Cleaner()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.classifier = ClassifierPipeline()
        self.exporter = ExporterPipeline()

        self.fetcher: Fetcher | None = None
        self.results: list[Post] = []

    def start(self, urls: list[str]) -> None:
        if self._is_running:
            logger.warning("Scraper is already running.")
            return

        self._is_running = True
        self.cancellation_token = CancellationToken()
        self.results = []

        self._worker_thread = threading.Thread(
            target=self._run_async_loop_in_thread,
            args=(urls,),
            daemon=True,
            name="ScraperBackgroundThread",
        )
        self._worker_thread.start()
        logger.info("Background thread started for scraper engine.")

    def _run_async_loop_in_thread(self, urls: list[str]) -> None:
        self._async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._async_loop)

        # Initialize fetcher within the event loop thread
        self.fetcher = Fetcher()

        try:
            self._async_loop.run_until_complete(self._execute_pipeline(urls))
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        finally:
            self._shutdown_gracefully()

    async def _execute_pipeline(self, urls: list[str]) -> None:
        logger.info(f"Starting pipeline for {len(urls)} URLs")

        for url in urls:
            if self.cancellation_token.is_cancelled:
                logger.info("Cancellation requested. Aborting pipeline.")
                break

            while self.cancellation_token.is_paused:
                if self.cancellation_token.is_cancelled:
                    break
                await asyncio.sleep(0.5)

            try:
                self._metrics_queue.put({"status": "processing", "url": url})
                await self._process_single_url(url)
                self._metrics_queue.put({"status": "success", "url": url})
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                self._metrics_queue.put(
                    {"status": "error", "url": url, "error": str(e)}
                )

        # Export at the end
        if self.results:
            try:
                self.exporter.export(self.results)
                self._metrics_queue.put(
                    {"status": "exported", "count": len(self.results)}
                )
            except Exception as e:
                logger.error(f"Export failed: {e}")

    async def _process_single_url(self, url: str) -> None:
        domain = urlparse(url).netloc.replace("www.", "")

        # 1. Fetch
        if not self.fetcher:
            raise RuntimeError("Fetcher not initialized")
        html = await self.fetcher.fetch(url)

        # 2. Parse
        post = self.parser.parse(html, url, domain)

        # 3. Validate
        post = self.validator.validate(post)

        # 4. Clean & 5. Normalize
        post = self.cleaner.clean(post)
        post = self.normalizer.normalize(post)

        # 6. Deduplicate
        if self.deduplicator.is_duplicate(post):
            logger.info(f"Duplicate post skipped: {post.id}")
            return

        # 7. Classify
        # For simplicity, we just add the category as a runtime attribute or skip it if model doesn't support it.
        # Actually our models.py Post doesn't have a category field. Let's just log it.
        category = self.classifier.classify(post)
        logger.info(f"Post {post.id} classified as {category}")

        self.results.append(post)

    def _shutdown_gracefully(self) -> None:
        logger.info("Commencing graceful shutdown...")
        self._is_running = False

        if self._async_loop and self._async_loop.is_running():
            # Close fetcher resources
            if self.fetcher:
                self._async_loop.run_until_complete(self.fetcher.close())

            pending_tasks = asyncio.all_tasks(self._async_loop)
            for task in pending_tasks:
                task.cancel()

            self._async_loop.run_until_complete(
                asyncio.gather(*pending_tasks, return_exceptions=True)
            )
            self._async_loop.close()
            logger.info("Async event loop closed gracefully.")

    def stop(self) -> None:
        if not self._is_running:
            return
        self.cancellation_token.cancel()

    def pause(self) -> None:
        self.cancellation_token.pause()

    def resume(self) -> None:
        self.cancellation_token.resume()

    def get_metrics(self) -> list[dict]:
        metrics = []
        while not self._metrics_queue.empty():
            try:
                metrics.append(self._metrics_queue.get_nowait())
            except Empty:
                break
        return metrics

    @property
    def is_running(self) -> bool:
        return self._is_running
