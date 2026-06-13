"""
dynamic_scraper.py
------------------
Developer-built: Playwright-based scraper for JavaScript-heavy pages.
Handles SPAs, lazy-loaded content, and pages that require JS execution.
AI does NOT run here — this is browser automation infrastructure.
"""

import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


def scrape_dynamic(url: str, wait_for: str = "networkidle", timeout: int = 30000) -> Optional[str]:
    """
    Scrape a dynamic/JS-rendered page using Playwright (sync wrapper).

    Args:
        url: The target URL to scrape.
        wait_for: Playwright wait_until condition — 'networkidle', 'domcontentloaded', or 'load'.
        timeout: Maximum wait time in milliseconds.

    Returns:
        Full rendered HTML as string, or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

        with sync_playwright() as p:
            # Launch Chromium in headless mode (no GUI)
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            # Create a context with realistic viewport and user-agent
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
            )

            page = context.new_page()

            try:
                logger.info(f"[DynamicScraper] Navigating to: {url}")
                page.goto(url, wait_until=wait_for, timeout=timeout)

                # Extra wait to ensure dynamic content finishes loading
                page.wait_for_load_state("networkidle", timeout=timeout)

                html = page.content()
                logger.info(f"[DynamicScraper] Successfully rendered {url}")
                return html

            except PlaywrightTimeout:
                logger.warning(f"[DynamicScraper] Timeout for {url}, returning partial content")
                # Still try to get whatever content loaded
                try:
                    return page.content()
                except Exception:
                    return None

            finally:
                context.close()
                browser.close()

    except ImportError:
        logger.error("[DynamicScraper] Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        logger.error(f"[DynamicScraper] Unexpected error for {url}: {e}")
        return None


def scrape_dynamic_with_scroll(url: str, scroll_count: int = 3, timeout: int = 30000) -> Optional[str]:
    """
    Scrape a page with infinite scroll by simulating scroll actions.

    Args:
        url: The target URL.
        scroll_count: Number of scroll-to-bottom actions to perform.
        timeout: Max wait time in milliseconds.

    Returns:
        Rendered HTML after scrolling, or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # Simulate scrolling to trigger lazy-loaded content
                for i in range(scroll_count):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1500)  # Wait 1.5s per scroll
                    logger.debug(f"[DynamicScraper] Scroll {i+1}/{scroll_count} done")

                html = page.content()
                logger.info(f"[DynamicScraper] Scroll scrape complete for {url}")
                return html

            finally:
                context.close()
                browser.close()

    except Exception as e:
        logger.error(f"[DynamicScraper] Scroll scrape failed for {url}: {e}")
        return None
