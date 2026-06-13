"""
client.py
---------
Developer-built: Gemini API wrapper using google-genai library.
Updated to gemini-2.5-flash model.
AI runs here — this is the bridge to Google Gemini.
"""

import os
import time
import logging
from typing import Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Updated to Gemini 2.5 Flash
GEMINI_MODEL = "gemini-2.5-flash"


class GeminiClient:
    """
    Wrapper around google-genai for Gemini 2.5 Flash.
    Developer: API key management, retry logic, error handling.
    AI: content generation, summarization, extraction, Q&A.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in the sidebar or .env file.\n"
                "Get your key at: https://aistudio.google.com/app/apikey"
            )
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model
        logger.info(f"[GeminiClient] Initialized with model: {model}")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        """Send a prompt to Gemini and return the text response."""
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"[GeminiClient] Sending prompt (attempt {attempt}/{max_retries})")
                config = types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192,
                    system_instruction=system_instruction,
                )
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                text = response.text
                logger.info(f"[GeminiClient] Response: {len(text)} chars")
                return text

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "quota" in error_str or "rate" in error_str or "429" in error_str:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(f"[GeminiClient] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                elif attempt < max_retries:
                    logger.warning(f"[GeminiClient] Attempt {attempt} failed: {e}. Retrying...")
                    time.sleep(retry_delay)

        logger.error(f"[GeminiClient] All {max_retries} attempts failed: {last_error}")
        raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {last_error}")

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


_client_instance: Optional[GeminiClient] = None


def get_client() -> GeminiClient:
    """Get or create singleton GeminiClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GeminiClient()
    return _client_instance