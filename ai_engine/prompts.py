"""
prompts.py
----------
Developer-built: Centralized repository of all prompt templates.
Prompts are carefully engineered to produce consistent, structured outputs from Gemini.
AI uses these prompts as instructions — this file defines HOW AI should behave.
"""

# ── SYSTEM INSTRUCTIONS ──────────────────────────────────────────────────────

SYSTEM_SCRAPING_ASSISTANT = """You are an expert web content analyst. 
Your job is to analyze scraped web content and provide accurate, structured, 
and useful information. Be concise, factual, and focus only on what is relevant.
Never hallucinate information that is not present in the provided content.
If the content is insufficient, say so clearly."""

SYSTEM_DATA_EXTRACTOR = """You are a precise data extraction engine.
Your job is to extract structured information from web content and return it 
as valid JSON only. Never add commentary outside the JSON. 
If a field is not found, use null. Always return well-formed JSON."""

SYSTEM_QA_ASSISTANT = """You are a helpful assistant that answers questions 
based strictly on the provided web page content. 
If the answer is not in the content, say "I couldn't find that information in the provided content."
Do not speculate beyond what the text says."""


# ── SUMMARIZATION PROMPTS ─────────────────────────────────────────────────────

def get_summarize_prompt(content: str, url: str = "", style: str = "concise") -> str:
    """
    Generate a summarization prompt.

    Args:
        content: Page text content to summarize.
        url: Source URL (for context).
        style: 'concise' (3-5 sentences), 'detailed' (full analysis), or 'bullets' (bullet points).

    Returns:
        Complete prompt string.
    """
    style_instructions = {
        "concise": "Write a concise summary in 3-5 sentences covering the main points.",
        "detailed": "Write a comprehensive summary covering: main topic, key arguments/findings, important details, and conclusions.",
        "bullets": "Summarize as a structured bullet list with: • Main topic, • Key points (5-8 bullets), • Key takeaway.",
    }

    instruction = style_instructions.get(style, style_instructions["concise"])

    url_context = f"\nSource URL: {url}" if url else ""

    return f"""Analyze the following web page content and provide a summary.{url_context}

{instruction}

--- WEB PAGE CONTENT ---
{content}
--- END CONTENT ---

Summary:"""


def get_chunk_summarize_prompt(chunk: str, chunk_num: int, total_chunks: int) -> str:
    """
    Prompt for summarizing a single chunk within a multi-chunk document.

    Args:
        chunk: Text chunk content.
        chunk_num: Current chunk index (1-based).
        total_chunks: Total number of chunks.

    Returns:
        Chunk summarization prompt.
    """
    return f"""This is part {chunk_num} of {total_chunks} from a web page.
Extract and list the KEY POINTS from this section only.
Be concise. Use bullet points. Focus on facts and important information.

--- CONTENT (Part {chunk_num}/{total_chunks}) ---
{chunk}
--- END ---

Key points from this section:"""


def get_merge_summaries_prompt(partial_summaries: list[str], url: str = "") -> str:
    """
    Prompt to merge multiple chunk summaries into a final coherent summary.

    Args:
        partial_summaries: List of per-chunk summary strings.
        url: Source URL.

    Returns:
        Merge prompt string.
    """
    summaries_text = "\n\n".join(
        f"[Section {i+1}]\n{s}" for i, s in enumerate(partial_summaries)
    )

    url_context = f"\nSource: {url}" if url else ""

    return f"""You have been given key points extracted from different sections of a web page.{url_context}

Combine these into ONE coherent, well-structured summary. 
Remove duplicates. Maintain logical flow. Keep it comprehensive but concise.

--- SECTION SUMMARIES ---
{summaries_text}
--- END ---

Final Summary:"""


# ── EXTRACTION PROMPTS ────────────────────────────────────────────────────────

def get_extract_prompt(content: str, extraction_schema: str, url: str = "") -> str:
    """
    Generate a data extraction prompt that returns structured JSON.

    Args:
        content: Page text content.
        extraction_schema: JSON schema or field description of what to extract.
        url: Source URL.

    Returns:
        Extraction prompt string.
    """
    url_context = f"\nSource URL: {url}" if url else ""

    return f"""Extract the specified information from the web page content below.
Return ONLY a valid JSON object or JSON array. No explanation, no markdown, just JSON.{url_context}

Required fields / schema:
{extraction_schema}

Rules:
- Use null for missing fields
- Use empty array [] if a list field has no items
- Dates in ISO format (YYYY-MM-DD) if possible
- Numbers as numeric types, not strings
- Return an array if multiple records exist

--- WEB PAGE CONTENT ---
{content}
--- END CONTENT ---

JSON Output:"""


def get_smart_extract_prompt(content: str, url: str = "") -> str:
    """
    Prompt for AI to auto-detect and extract the most relevant structured data
    (products, articles, jobs, events, etc.) without a fixed schema.

    Args:
        content: Page text content.
        url: Source URL.

    Returns:
        Smart extraction prompt.
    """
    return f"""Analyze this web page content and extract all structured, meaningful data you find.
Automatically detect the content type (product, article, job listing, event, directory, etc.).
Return ONLY valid JSON. No markdown. No explanation.

Structure your response as:
{{
  "content_type": "detected type",
  "extracted_data": [... array of records ...],
  "fields_found": ["list", "of", "fields", "extracted"]
}}

--- WEB PAGE CONTENT ---
{content}
--- END CONTENT ---

JSON:"""


# ── Q&A PROMPTS ───────────────────────────────────────────────────────────────

def get_qa_prompt(content: str, question: str, url: str = "") -> str:
    """
    Generate a question-answering prompt grounded in scraped content.

    Args:
        content: Page text content (the knowledge base).
        question: User's question.
        url: Source URL.

    Returns:
        Q&A prompt string.
    """
    url_context = f"\nSource: {url}" if url else ""

    return f"""Answer the question based ONLY on the web page content provided below.
Be specific and direct. Quote relevant parts when helpful.{url_context}

Question: {question}

--- WEB PAGE CONTENT ---
{content}
--- END CONTENT ---

Answer:"""


def get_multi_chunk_qa_prompt(chunks_with_relevance: list[str], question: str) -> str:
    """
    Q&A prompt when relevant sections from multiple chunks are provided.

    Args:
        chunks_with_relevance: List of relevant text sections.
        question: User's question.

    Returns:
        Multi-chunk Q&A prompt.
    """
    context = "\n\n---\n\n".join(chunks_with_relevance)

    return f"""Answer the following question using the relevant web page sections provided.
Be accurate and specific. Only use information from the provided content.

Question: {question}

--- RELEVANT CONTENT SECTIONS ---
{context}
--- END ---

Answer:"""
