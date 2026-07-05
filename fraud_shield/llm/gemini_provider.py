"""Gemini LLM Provider implementing the ModelProvider interface.

Uses the official google-genai SDK to connect to Google Gemini.
"""

import json
import logging
from typing import List, Type, TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types

from fraud_shield.interfaces import ModelProvider

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class GeminiModelProvider(ModelProvider):
    """Gemini-powered ModelProvider using google-genai client."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """Initializes the provider with the user API key and model name.
        
        Args:
            api_key: The Gemini API key.
            model_name: The model identifier (default: gemini-2.5-flash).
        """
        self.api_key = api_key
        self.model_name = model_name
        self.is_mock = False
        logger.info(f"Initialized GeminiModelProvider with model: {model_name}")

    def generate_json(self, prompt: str, response_schema: Type[T]) -> T:
        """Queries Gemini to get structured JSON output matching the Pydantic schema."""
        logger.info(f"GeminiModelProvider querying structured generation using model {self.model_name}...")
        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,  # Low temperature for highly structured consistency
                )
            )
            text_output = response.text
            logger.debug(f"Raw Gemini JSON response: {text_output}")
            
            # Parse text as Pydantic model
            return response_schema.model_validate_json(text_output)
        except Exception as e:
            logger.error(f"Error during Gemini generate_json: {str(e)}", exc_info=True)
            raise

    def classify(self, content: str, categories: List[str]) -> str:
        """Classify a piece of text into one of the specified categories."""
        logger.info(f"GeminiModelProvider classifying query into {categories}...")
        prompt = f"""
        Classify the following content into exactly one of these categories: {', '.join(categories)}.
        Return only the category name, without any explanations, markdown, or punctuation.
        
        Content:
        "{content}"
        """
        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            result = response.text.strip().lower()
            
            # Match the response against provided categories
            for cat in categories:
                if cat.lower() in result or result in cat.lower():
                    return cat
            return categories[0]
        except Exception as e:
            logger.error(f"Error during Gemini classification: {str(e)}")
            return categories[0]
