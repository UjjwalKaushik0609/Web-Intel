"""
test_pipeline.py
----------------
Unit tests for pipeline modules.
Tests caching, deduplication, exporting, and pipeline orchestration.
AI calls are mocked to avoid real API usage in tests.
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFileCache(unittest.TestCase):
    """Tests for pipeline/cache.py — TTL file cache."""

    def setUp(self):
        """Create a temporary directory for cache files."""
        self.temp_dir = tempfile.mkdtemp()

    def test_set_and_get(self):
        """Should store and retrieve data correctly."""
        from pipeline.cache import FileCache

        cache = FileCache(cache_dir=self.temp_dir, ttl=3600)
        cache.set("https://example.com", {"data": "test value"})
        result = cache.get("https://example.com")

        self.assertIsNotNone(result)
        self.assertEqual(result["data"], "test value")

    def test_cache_miss_returns_none(self):
        """Should return None for non-existent cache key."""
        from pipeline.cache import FileCache

        cache = FileCache(cache_dir=self.temp_dir, ttl=3600)
        result = cache.get("https://notcached.com")

        self.assertIsNone(result)

    def test_ttl_expiration(self):
        """Should return None for expired cache entries."""
        import time
        from pipeline.cache import FileCache

        cache = FileCache(cache_dir=self.temp_dir, ttl=1)  # 1 second TTL
        cache.set("https://example.com/expire", "data")

        # Data should exist immediately
        self.assertIsNotNone(cache.get("https://example.com/expire"))

        # Wait for TTL to expire
        time.sleep(2)
        result = cache.get("https://example.com/expire")
        self.assertIsNone(result)

    def test_cache_invalidate(self):
        """Should delete a specific cache entry."""
        from pipeline.cache import FileCache

        cache = FileCache(cache_dir=self.temp_dir, ttl=3600)
        cache.set("https://example.com", "data")
        cache.invalidate("https://example.com")

        self.assertIsNone(cache.get("https://example.com"))

    def test_cache_stats(self):
        """Should return valid stats dict."""
        from pipeline.cache import FileCache

        cache = FileCache(cache_dir=self.temp_dir, ttl=3600)
        cache.set("https://a.com", "data1")
        cache.set("https://b.com", "data2")
        stats = cache.stats()

        self.assertIn("total_entries", stats)
        self.assertIn("valid_entries", stats)
        self.assertGreaterEqual(stats["total_entries"], 2)

    def test_clear_all(self):
        """Should delete all cache files."""
        from pipeline.cache import FileCache

        cache = FileCache(cache_dir=self.temp_dir, ttl=3600)
        cache.set("https://a.com", "data1")
        cache.set("https://b.com", "data2")

        count = cache.clear_all()
        self.assertGreaterEqual(count, 2)
        self.assertIsNone(cache.get("https://a.com"))


class TestDeduplicator(unittest.TestCase):
    """Tests for pipeline/deduplicator.py — record deduplication."""

    def test_removes_exact_duplicates(self):
        """Should remove identical records."""
        from pipeline.deduplicator import deduplicate

        records = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Alice", "age": 30},  # Duplicate
        ]
        result = deduplicate(records)
        self.assertEqual(len(result), 2)

    def test_dedup_by_key_fields(self):
        """Should deduplicate based on specific key fields only."""
        from pipeline.deduplicator import deduplicate

        records = [
            {"url": "https://a.com", "title": "A", "scraped_at": "2024-01-01"},
            {"url": "https://b.com", "title": "B", "scraped_at": "2024-01-01"},
            {"url": "https://a.com", "title": "A Updated", "scraped_at": "2024-01-02"},  # Same URL = duplicate
        ]
        result = deduplicate(records, key_fields=["url"])
        self.assertEqual(len(result), 2)

    def test_empty_list_returns_empty(self):
        """Should handle empty input gracefully."""
        from pipeline.deduplicator import deduplicate

        result = deduplicate([])
        self.assertEqual(result, [])

    def test_no_duplicates_unchanged(self):
        """Should return all records if none are duplicates."""
        from pipeline.deduplicator import deduplicate

        records = [{"id": i, "name": f"Item {i}"} for i in range(5)]
        result = deduplicate(records)
        self.assertEqual(len(result), 5)

    def test_find_duplicates(self):
        """Should identify duplicate groups."""
        from pipeline.deduplicator import find_duplicates

        records = [
            {"name": "X"},
            {"name": "Y"},
            {"name": "X"},  # Duplicate of first
        ]
        groups = find_duplicates(records)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 2)

    def test_merge_and_deduplicate(self):
        """Should merge multiple lists and deduplicate."""
        from pipeline.deduplicator import merge_and_deduplicate

        list1 = [{"id": 1}, {"id": 2}]
        list2 = [{"id": 2}, {"id": 3}]  # id=2 is duplicate
        result = merge_and_deduplicate(list1, list2)
        self.assertEqual(len(result), 3)


class TestExporter(unittest.TestCase):
    """Tests for pipeline/exporter.py — data export."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_export_to_json(self):
        """Should create a valid JSON file."""
        from pipeline.exporter import export_to_json

        data = [{"name": "Alice", "score": 100}, {"name": "Bob", "score": 90}]
        filepath = export_to_json(data, filename="test.json", export_dir=self.temp_dir)

        self.assertTrue(os.path.exists(filepath))
        with open(filepath) as f:
            loaded = json.load(f)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["name"], "Alice")

    def test_export_to_csv(self):
        """Should create a valid CSV file."""
        from pipeline.exporter import export_to_csv

        data = [{"product": "Widget", "price": 9.99}, {"product": "Gadget", "price": 19.99}]
        filepath = export_to_csv(data, filename="test.csv", export_dir=self.temp_dir)

        self.assertTrue(os.path.exists(filepath))

        import pandas as pd
        df = pd.read_csv(filepath)
        self.assertEqual(len(df), 2)
        self.assertIn("product", df.columns)
        self.assertIn("price", df.columns)

    def test_export_to_dataframe(self):
        """Should return a pandas DataFrame."""
        import pandas as pd
        from pipeline.exporter import export_to_dataframe

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        df = export_to_dataframe(data)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn("a", df.columns)

    def test_flatten_nested_for_csv(self):
        """Should flatten nested dicts for CSV export."""
        from pipeline.exporter import export_to_csv

        data = [{"name": "Test", "meta": {"category": "A", "tags": ["x", "y"]}}]
        filepath = export_to_csv(data, filename="nested.csv", export_dir=self.temp_dir, flatten=True)

        import pandas as pd
        df = pd.read_csv(filepath)
        # Flattened key should exist
        self.assertTrue(any("meta" in col for col in df.columns))


class TestPipeline(unittest.TestCase):
    """Integration tests for pipeline/pipeline.py — master orchestrator."""

    @patch("pipeline.pipeline.scrape_static")
    @patch("pipeline.pipeline.detect_page_type")
    def test_fetch_content_static(self, mock_detect, mock_scrape):
        """Should fetch content using static scraper."""
        from bs4 import BeautifulSoup
        from pipeline.pipeline import ScrapingPipeline

        # Mock detection and scraping
        mock_detect.return_value = "static"
        mock_soup = BeautifulSoup("<html><body><p>Test content here</p></body></html>", "html.parser")
        mock_scrape.return_value = mock_soup

        pipeline = ScrapingPipeline(use_cache=False)
        content = pipeline.fetch_content("https://example.com")

        self.assertIsNotNone(content)
        self.assertIn("Test content", content)

    @patch("pipeline.pipeline.scrape_static")
    @patch("pipeline.pipeline.detect_page_type")
    def test_fetch_content_failure_returns_none(self, mock_detect, mock_scrape):
        """Should return None when all scraping strategies fail."""
        from pipeline.pipeline import ScrapingPipeline

        mock_detect.return_value = "static"
        mock_scrape.return_value = None

        with patch("pipeline.pipeline.scrape_dynamic") as mock_dynamic:
            mock_dynamic.return_value = None
            pipeline = ScrapingPipeline(use_cache=False)
            content = pipeline.fetch_content("https://failing.com")

        self.assertIsNone(content)

    @patch("pipeline.pipeline.scrape_static")
    @patch("pipeline.pipeline.detect_page_type")
    def test_run_summarize_with_mocked_ai(self, mock_detect, mock_scrape):
        """Should return summary result with mocked AI response."""
        from bs4 import BeautifulSoup
        from pipeline.pipeline import ScrapingPipeline

        mock_detect.return_value = "static"
        mock_soup = BeautifulSoup(
            "<html><body><p>" + "This is test content. " * 50 + "</p></body></html>",
            "html.parser"
        )
        mock_scrape.return_value = mock_soup

        pipeline = ScrapingPipeline(use_cache=False)

        # Mock the AI client
        mock_client = MagicMock()
        mock_client.generate.return_value = "This is a mocked summary from Gemini."
        pipeline._ai_client = mock_client

        with patch("pipeline.pipeline.summarize") as mock_summarize:
            mock_summarize.return_value = "This is a mocked summary from Gemini."
            result = pipeline.run_summarize("https://example.com", style="concise")

        self.assertIn("summary", result)
        self.assertEqual(result["url"], "https://example.com")


if __name__ == "__main__":
    unittest.main(verbosity=2)
