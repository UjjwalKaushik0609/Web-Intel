"""
chunker.py
----------
Developer-built: Token-safe text splitting for feeding content to Gemini API.
Gemini 1.5 Flash supports large context, but chunking ensures cost efficiency
and avoids hitting API limits for very long pages.
AI does NOT run here — pure text processing logic.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# Conservative character limits (chars ≈ 4× tokens for English text)
DEFAULT_CHUNK_SIZE = 6000   # ~1500 tokens per chunk
DEFAULT_OVERLAP = 200       # Overlap to preserve context between chunks
MAX_CHUNK_SIZE = 20000      # Hard cap per chunk (~5000 tokens)


def split_by_paragraphs(text: str, max_chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> List[str]:
    """
    Split text into chunks at paragraph boundaries to preserve context.

    Strategy:
    1. Split on double newlines (paragraph breaks)
    2. Accumulate paragraphs until chunk size is reached
    3. Add overlap from previous chunk to maintain continuity

    Args:
        text: Plain text to split.
        max_chunk_size: Maximum characters per chunk.
        overlap: Characters to overlap between chunks.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    # Split on paragraph boundaries (double newlines)
    paragraphs = re.split(r"\n\n+", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = ""
    previous_tail = ""  # Overlap from previous chunk

    for para in paragraphs:
        # If a single paragraph exceeds max size, force-split it
        if len(para) > max_chunk_size:
            # First flush current chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
                previous_tail = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = ""

            # Split the long paragraph by sentences
            sentence_chunks = split_by_sentences(para, max_chunk_size, overlap)
            chunks.extend(sentence_chunks)
            if sentence_chunks:
                previous_tail = sentence_chunks[-1][-overlap:] if len(sentence_chunks[-1]) > overlap else sentence_chunks[-1]
            continue

        # Check if adding this paragraph exceeds limit
        candidate = (previous_tail + "\n\n" + current_chunk + "\n\n" + para).strip() if not current_chunk else (current_chunk + "\n\n" + para)

        if len(candidate) > max_chunk_size and current_chunk:
            # Save current chunk and start new one
            chunks.append(current_chunk.strip())
            previous_tail = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = (previous_tail + "\n\n" + para).strip()
        else:
            current_chunk = candidate

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    logger.info(f"[Chunker] Split {len(text)} chars into {len(chunks)} chunks")
    return chunks


def split_by_sentences(text: str, max_chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> List[str]:
    """
    Split text into chunks at sentence boundaries.

    Args:
        text: Plain text to split.
        max_chunk_size: Maximum characters per chunk.
        overlap: Characters to overlap between chunks.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    # Simple sentence boundary detection
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_text(text: str, strategy: str = "paragraphs", max_size: int = DEFAULT_CHUNK_SIZE) -> List[str]:
    """
    Main chunking entry point. Auto-selects strategy based on text structure.

    Args:
        text: Text to chunk.
        strategy: 'paragraphs' or 'sentences'.
        max_size: Max characters per chunk.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    # If text fits in one chunk, return as-is
    if len(text) <= max_size:
        return [text]

    if strategy == "sentences":
        return split_by_sentences(text, max_size)
    else:
        return split_by_paragraphs(text, max_size)


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimate (chars / 4 for English text).
    Used to warn if content might exceed model limits.

    Args:
        text: Input text.

    Returns:
        Estimated token count.
    """
    return max(1, len(text) // 4)
