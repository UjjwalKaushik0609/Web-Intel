"""
test_scraper.py
---------------
Unit tests for scraper modules.
Tests static scraping, HTML cleaning, chunking, and detection logic.
Uses mock responses to avoid real network calls in CI/CD.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCleaner(unittest.TestCase):
    """Tests for scraper/cleaner.py — HTML to text conversion."""

    def test_basic_html_to_text(self):
        """Should extract text from simple HTML."""
        from scraper.cleaner import html_to_text

        html = "<html><body><h1>Hello World</h1><p>This is a test.</p></body></html>"
        result = html_to_text(html)

        self.assertIn("Hello World", result)
        self.assertIn("This is a test", result)

    def test_strips_script_tags(self):
        """Should remove JavaScript from extracted text."""
        from scraper.cleaner import html_to_text

        html = "<html><body><p>Content</p><script>alert('hello');</script></body></html>"
        result = html_to_text(html)

        self.assertIn("Content", result)
        self.assertNotIn("alert", result)

    def test_strips_style_tags(self):
        """Should remove CSS from extracted text."""
        from scraper.cleaner import html_to_text

        html = "<html><head><style>body { color: red; }</style></head><body><p>Text</p></body></html>"
        result = html_to_text(html)

        self.assertIn("Text", result)
        self.assertNotIn("color: red", result)

    def test_empty_html_returns_empty_string(self):
        """Should return empty string for empty input."""
        from scraper.cleaner import html_to_text

        result = html_to_text("")
        self.assertEqual(result, "")

    def test_extract_metadata_title(self):
        """Should extract page title from BeautifulSoup."""
        from bs4 import BeautifulSoup
        from scraper.cleaner import extract_metadata

        html = "<html><head><title>My Page Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        metadata = extract_metadata(soup)

        self.assertEqual(metadata["title"], "My Page Title")

    def test_extract_metadata_description(self):
        """Should extract meta description."""
        from bs4 import BeautifulSoup
        from scraper.cleaner import extract_metadata

        html = '<html><head><meta name="description" content="Page about AI"/></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        metadata = extract_metadata(soup)

        self.assertEqual(metadata["description"], "Page about AI")


class TestChunker(unittest.TestCase):
    """Tests for scraper/chunker.py — text splitting logic."""

    def test_short_text_single_chunk(self):
        """Short text should return a single chunk."""
        from scraper.chunker import chunk_text

        text = "This is a short text."
        chunks = chunk_text(text, max_size=1000)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_long_text_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        from scraper.chunker import chunk_text

        text = "This is a paragraph.\n\n" * 100  # Create long text with paragraphs
        chunks = chunk_text(text, max_size=200)

        self.assertGreater(len(chunks), 1)

    def test_chunks_contain_all_content(self):
        """All original content should be present across chunks."""
        from scraper.chunker import chunk_text

        sentences = [f"Sentence number {i}." for i in range(20)]
        text = " ".join(sentences)
        chunks = chunk_text(text, max_size=100)

        combined = " ".join(chunks)
        # Check that meaningful content is preserved (some overlap may occur)
        self.assertGreater(len(combined), len(text) * 0.8)

    def test_empty_text_returns_empty(self):
        """Empty text should return empty list."""
        from scraper.chunker import chunk_text

        chunks = chunk_text("")
        self.assertEqual(chunks, [])

    def test_estimate_tokens(self):
        """Token estimation should return positive integer."""
        from scraper.chunker import estimate_tokens

        token_count = estimate_tokens("This is a test sentence with several words.")
        self.assertGreater(token_count, 0)
        self.assertIsInstance(token_count, int)


class TestDetector(unittest.TestCase):
    """Tests for scraper/detector.py — static vs dynamic detection."""

    def test_known_static_domain(self):
        """Wikipedia should be detected as static."""
        from scraper.detector import detect_page_type

        # Mock the HEAD request to avoid network calls
        with patch("scraper.detector._quick_fetch_head") as mock_head:
            mock_head.return_value = {"content_type": "text/html", "status_code": 200}
            result = detect_page_type("https://en.wikipedia.org/wiki/Python")

        self.assertEqual(result, "static")

    def test_known_dynamic_domain(self):
        """Twitter/X should be detected as dynamic."""
        from scraper.detector import detect_page_type

        result = detect_page_type("https://twitter.com/user")
        self.assertEqual(result, "dynamic")

    def test_js_framework_detection(self):
        """HTML with React root should be detected as dynamic."""
        from scraper.detector import detect_page_type

        sample_html = '<html><body><div id="root"></div><script>__NEXT_DATA__ = {};</script></body></html>'

        with patch("scraper.detector._quick_fetch_head") as mock_head:
            mock_head.return_value = {"content_type": "text/html", "status_code": 200}
            result = detect_page_type("https://unknown-spa-site.com", sample_html=sample_html)

        self.assertEqual(result, "dynamic")

    def test_default_to_static(self):
        """Unknown domains without JS patterns should default to static."""
        from scraper.detector import detect_page_type

        with patch("scraper.detector._quick_fetch_head") as mock_head:
            mock_head.return_value = {"content_type": "text/html", "status_code": 200}
            result = detect_page_type("https://some-plain-html-blog.com")

        self.assertEqual(result, "static")


class TestBaseScraper(unittest.TestCase):
    """Tests for scraper/base_scraper.py — static HTTP scraping."""

    @patch("scraper.base_scraper.requests.Session")
    def test_successful_static_scrape(self, mock_session_class):
        """Should return BeautifulSoup on successful HTTP response."""
        from scraper.base_scraper import scrape_static

        # Mock the session and response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Test content</p></body></html>"
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        with patch("scraper.base_scraper.time.sleep"):  # Skip delay in tests
            result = scrape_static("https://example.com", delay=0)

        self.assertIsNotNone(result)

    @patch("scraper.base_scraper.requests.Session")
    def test_failed_scrape_returns_none(self, mock_session_class):
        """Should return None on connection error."""
        import requests
        from scraper.base_scraper import scrape_static

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("No connection")
        mock_session_class.return_value = mock_session

        with patch("scraper.base_scraper.time.sleep"):
            result = scrape_static("https://nonexistent.example.com", delay=0)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
