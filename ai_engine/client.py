"""
client.py
---------
Developer-built: Gemini API wrapper.
SECURITY FIX: Removed global singleton. Every call creates a fresh client
scoped to the api_key passed in — prevents one visitor's key leaking to
another visitor on a shared/public deployment.
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

GEMINI_MODEL = "gemini-2.5-flash"


class GeminiClient:
    """Wrapper around google-genai for Gemini 2.5 Flash."""

    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No Gemini API key provided. Enter your key in the sidebar.\n"
                "Get one free at: https://aistudio.google.com/app/apikey"
            )
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model
        logger.info(f"[GeminiClient] Initialized fresh client (model={model})")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                config = types.GenerateContentConfig(
                    temperature=0.3, top_p=0.8, top_k=40,
                    max_output_tokens=8192,
                    system_instruction=system_instruction,
                )
                response = self.client.models.generate_content(
                    model=self.model_name, contents=prompt, config=config,
                )
                return response.text
            except Exception as e:
                last_error = e
                err = str(e).lower()
                if "quota" in err or "rate" in err or "429" in err:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(f"[GeminiClient] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                elif attempt < max_retries:
                    time.sleep(retry_delay)
        raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {last_error}")

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


def get_client(api_key: Optional[str] = None) -> GeminiClient:
    """
    Create a FRESH GeminiClient scoped to the given api_key.

    SECURITY: No caching/singleton here on purpose. Each Streamlit session
    must pass its own api_key explicitly (from st.session_state), so one
    visitor's key can never bleed into another visitor's requests.
    """
    return GeminiClient(api_key=api_key)