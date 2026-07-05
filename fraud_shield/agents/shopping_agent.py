"""Shopping Trust Sub-Agent.

Analyzes e-commerce websites, pricing deals, reviews, and storefront signals
to identify fraudulent shops, counterfeit vendors, and data-stealing platforms.
"""

import logging
from typing import Optional
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult, ModelProvider
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="Shopping Trust Agent",
    description="Evaluates online shopping sites and discount offers for counterfeit, scam storefront, and pricing red flags."
)
class ShoppingTrustAgent(BaseSubAgent):
    """Sub-agent specialized in identifying fraudulent shopping storefronts."""

    @property
    def name(self) -> str:
        return "Shopping Trust Agent"

    @property
    def description(self) -> str:
        return "Evaluates online shopping sites and discount offers for counterfeit, scam storefront, and pricing red flags."

    def analyze(self, content: str, model_provider: Optional[ModelProvider] = None) -> AgentResult:
        logger.info(f"Running shopping trust analysis on: {content[:40]}...")
        
        # Check if we should use Live Gemini AI
        if model_provider and not getattr(model_provider, "is_mock", True):
            prompt = f"""
            You are the 'Shopping Trust Agent' in the AI Fraud Shield cybersecurity system.
            Analyze the following query or website description for online shopping scams, suspicious discounts, counterfeit sellers, scam storefronts, missing refund policies, and card-harvesting risks.
            
            Content to Analyze:
            "{content}"
            
            Evaluate the overall risk_level (LOW, MEDIUM, HIGH, CRITICAL), assign a confidence score (0.0 to 1.0), and list specific findings as detailed bullet points.
            Include the key 'is_shopping_intent' with a boolean value in the details object.
            Output strictly in JSON matching the requested AgentResult schema.
            """
            try:
                return model_provider.generate_json(prompt, AgentResult)
            except Exception as e:
                logger.error(f"Gemini live analysis failed for {self.name}: {e}. Falling back to rule-based analysis.")

        # Fallback to local rule-based matching
        content_lower = content.lower()
        findings = []
        risk_level = "LOW"
        confidence = 0.82
        
        # Check shopping indicators
        if "discount" in content_lower or "off" in content_lower or "free" in content_lower or "cheap" in content_lower:
            if "90%" in content_lower or "95%" in content_lower or "unbelievable" in content_lower:
                findings.append("Extreme discounts detected (e.g. 90%+ off). This is highly characteristic of bait-and-switch or credit card harvesting stores.")
                risk_level = "HIGH"
            else:
                findings.append("Promotional deal or discount mentioned. Requires domain validation.")
                risk_level = "MEDIUM"
                
        if "no return policy" in content_lower or "no contact info" in content_lower:
            findings.append("Lack of business transparency: missing refund policy or contact details.")
            risk_level = "HIGH"
            
        if "out of stock" in content_lower and "preorder" in content_lower:
            findings.append("High pressure sales tactic: pre-ordering out-of-stock items under time constraints.")
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level

        if not findings:
            findings.append("No suspicious shopping trust indicators detected.")
            confidence = 0.65

        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"is_shopping_intent": True}
        )
