"""
summarizer.py
-------------
Developer-built: Orchestration layer that breaks long pages into chunks and
feeds them to Gemini for summarization, then merges the results.
AI runs inside this module via GeminiClient — Gemini does the actual summarizing.
"""

import logging
from typing import Optional

from ai_engine.client import GeminiClient, get_client
from ai_engine.prompts import (
    SYSTEM_SCRAPING_ASSISTANT,
    get_summarize_prompt,
    get_chunk_summarize_prompt,
    get_merge_summaries_prompt,
)
from scraper.chunker import chunk_text

logger = logging.getLogger(__name__)

# Max chars to send to Gemini in a single summarization call
SINGLE_PASS_LIMIT = 15000


def summarize(
    content: str,
    url: str = "",
    style: str = "concise",
    client: Optional[GeminiClient] = None,
) -> str:
    """
    Summarize web page content using Gemini 1.5 Flash.

    For short content: single Gemini call.
    For long content: chunk → summarize each → merge into final summary.

    Developer logic: chunking strategy, merge orchestration.
    AI logic: actual summarization of text (Gemini).

    Args:
        content: Cleaned page text.
        url: Source URL (for context in prompts).
        style: 'concise', 'detailed', or 'bullets'.
        client: Optional GeminiClient instance (creates one if not provided).

    Returns:
        Summary string.
    """
    if not content or not content.strip():
        return "No content available to summarize."

    client = client or get_client()

    # Short content — single API call
    if len(content) <= SINGLE_PASS_LIMIT:
        logger.info(f"[Summarizer] Single-pass summarization ({len(content)} chars)")
        prompt = get_summarize_prompt(content, url=url, style=style)
        return client.generate(prompt, system_instruction=SYSTEM_SCRAPING_ASSISTANT)

    # Long content — chunk and merge strategy
    logger.info(f"[Summarizer] Multi-pass summarization ({len(content)} chars)")
    chunks = chunk_text(content, strategy="paragraphs", max_size=8000)
    logger.info(f"[Summarizer] Split into {len(chunks)} chunks")

    # Step 1: Summarize each chunk independently
    partial_summaries = []
    for i, chunk in enumerate(chunks):
        logger.debug(f"[Summarizer] Summarizing chunk {i+1}/{len(chunks)}")
        try:
            prompt = get_chunk_summarize_prompt(chunk, i + 1, len(chunks))
            partial = client.generate(prompt, system_instruction=SYSTEM_SCRAPING_ASSISTANT)
            partial_summaries.append(partial)
        except Exception as e:
            logger.error(f"[Summarizer] Failed to summarize chunk {i+1}: {e}")
            partial_summaries.append(f"[Chunk {i+1} failed to process]")

    # Step 2: Merge all partial summaries into final output
    if len(partial_summaries) == 1:
        return partial_summaries[0]

    logger.info("[Summarizer] Merging partial summaries...")
    merge_prompt = get_merge_summaries_prompt(partial_summaries, url=url)
    final_summary = client.generate(
        merge_prompt,
        system_instruction=SYSTEM_SCRAPING_ASSISTANT,
    )

    return final_summary


def summarize_multiple_pages(
    pages: list[dict],
    style: str = "bullets",
    client: Optional[GeminiClient] = None,
) -> str:
    """
    Summarize multiple pages into a combined overview.

    Args:
        pages: List of dicts with 'url' and 'content' keys.
        style: Summary style.
        client: Optional GeminiClient.

    Returns:
        Combined summary string.
    """
    client = client or get_client()
    summaries = []

    for page in pages:
        url = page.get("url", "")
        content = page.get("content", "")
        if content:
            try:
                summary = summarize(content, url=url, style="bullets", client=client)
                summaries.append(f"**{url}**\n{summary}")
            except Exception as e:
                logger.error(f"[Summarizer] Failed for {url}: {e}")
                summaries.append(f"**{url}**\n[Failed to summarize]")

    if not summaries:
        return "No content could be summarized."

    # Final merge
    merged_prompt = get_merge_summaries_prompt(summaries)
    return client.generate(merged_prompt, system_instruction=SYSTEM_SCRAPING_ASSISTANT)
