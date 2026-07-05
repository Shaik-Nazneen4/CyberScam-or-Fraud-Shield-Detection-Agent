"""Mock LLM Provider implementing the ModelProvider interface.

Allows running the orchestrator without API keys/network connections by using
rule-based pattern matching to simulate LLM classifications and structured responses.
"""

import logging
import re
from typing import List, Type, TypeVar
from pydantic import BaseModel
from fraud_shield.interfaces import ModelProvider

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class MockModelProvider(ModelProvider):
    """Mock implementation of ModelProvider for offline capability and unit testing."""

    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        self.is_mock = True  # Signals agents to use rule-based fallback, not live Gemini
        logger.info(f"Initialized MockModelProvider with model name: {model_name}")

    def _determine_category(self, text: str) -> str:
        """Determines the category/input type of the request using keyword matching."""
        text_lower = text.lower()
        if "everything" in text_lower or re.search(r"\ball\b", text_lower) or "report" in text_lower:
            return "multi_risk_report"
        elif "internship" in text_lower or "job" in text_lower or "career" in text_lower:
            return "job_internship"
        elif "shop" in text_lower or "shopping" in text_lower or "store" in text_lower or "buy" in text_lower:
            return "shopping"
        elif "email" in text_lower or "phishing" in text_lower:
            return "email"
        elif "whatsapp" in text_lower or "message" in text_lower or "sms" in text_lower or "text" in text_lower:
            return "sms_whatsapp"
        elif "url" in text_lower or "website" in text_lower or "http" in text_lower or "link" in text_lower:
            return "url"
        elif "otp" in text_lower or "bank" in text_lower or "card" in text_lower:
            return "general_banking"
        else:
            return "general_query"

    def classify(self, content: str, categories: List[str]) -> str:
        """Mock classification based on simple string matching.
        
        Args:
            content: Text to classify.
            categories: Possible category labels.
            
        Returns:
            The matched category.
        """
        detected = self._determine_category(content)
        
        # Map detected to one of the provided categories if possible
        for cat in categories:
            if detected in cat.lower() or cat.lower() in detected:
                logger.debug(f"Classified '{content[:20]}...' as '{cat}'")
                return cat
                
        # Fallback to the first category if none match
        logger.debug(f"Classified '{content[:20]}...' as default '{categories[0]}'")
        return categories[0]

    def generate_json(self, prompt: str, response_schema: Type[T]) -> T:
        """Generates a mock JSON response adhering to the requested Pydantic schema.
        
        It inspects the prompt to find the user request and builds the schema dynamically.
        """
        logger.debug(f"MockModelProvider generating structured output for schema: {response_schema.__name__}")
        
        # Check if the schema is the RoutingDecision schema
        schema_name = response_schema.__name__
        
        # We can extract the user content from the prompt.
        # Usually prompts look like: ... User input: "..." ...
        content = prompt
        user_input_match = re.search(r'(?:user input|content|request):\s*["\'](.*?)["\']', prompt, re.IGNORECASE | re.DOTALL)
        if user_input_match:
            content = user_input_match.group(1)
            
        category = self._determine_category(content)
        
        if schema_name == "RoutingDecision" or "Routing" in schema_name:
            # We map categories to appropriate agents
            if category == "email":
                data = {
                    "input_type": "email",
                    "selected_agents": ["Email Scam Detection Agent"]
                }
            elif category == "sms_whatsapp":
                data = {
                    "input_type": "sms_whatsapp",
                    "selected_agents": ["SMS & WhatsApp Scam Detection Agent"]
                }
            elif category == "url":
                data = {
                    "input_type": "url",
                    "selected_agents": ["URL Analysis Agent"]
                }
            elif category == "shopping":
                data = {
                    "input_type": "shopping",
                    "selected_agents": ["Shopping Trust Agent"]
                }
            elif category == "job_internship":
                data = {
                    "input_type": "job_internship",
                    "selected_agents": ["Internship & Job Scam Detection Agent"]
                }
            elif category == "general_banking":
                data = {
                    "input_type": "general_banking",
                    "selected_agents": ["SMS & WhatsApp Scam Detection Agent", "Risk Score Agent", "Safety Advisor Agent"]
                }
            elif category == "multi_risk_report":
                data = {
                    "input_type": "multi_risk_report",
                    "selected_agents": [
                        "Email Scam Detection Agent",
                        "SMS & WhatsApp Scam Detection Agent",
                        "URL Analysis Agent",
                        "Shopping Trust Agent",
                        "Internship & Job Scam Detection Agent",
                        "Risk Score Agent",
                        "Safety Advisor Agent"
                    ]
                }
            else:
                data = {
                    "input_type": "general_query",
                    "selected_agents": ["Risk Score Agent", "Safety Advisor Agent"]
                }
            return response_schema(**data)
            
        elif schema_name == "CoordinatorResponse" or "Coordinator" in schema_name:
            # Fallback if coordinator response is requested directly from model
            data = {
                "input_type": category,
                "selected_agents": ["Mock Agent"],
                "analysis_status": "success",
                "overall_risk": "LOW",
                "recommendation": "Use caution with unsolicited contact.",
                "next_steps": ["Do not share private details."]
            }
            return response_schema(**data)
            
        # Generic fallback for any other schema
        # Try to construct default arguments for the schema fields
        fallback_data = {}
        for name, field in response_schema.model_fields.items():
            if field.annotation == str:
                fallback_data[name] = "mock_string"
            elif field.annotation == float:
                fallback_data[name] = 0.9
            elif getattr(field.annotation, "__origin__", None) is list:
                fallback_data[name] = []
            elif getattr(field.annotation, "__origin__", None) is dict:
                fallback_data[name] = {}
            else:
                fallback_data[name] = None
        return response_schema(**fallback_data)
