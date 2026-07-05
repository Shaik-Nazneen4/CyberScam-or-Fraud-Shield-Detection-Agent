"""Email Scam Detection Sub-Agent.

Analyzes text for indicators of email phishing, wire transfer fraud, lottery scams,
and impersonation attempts.
"""

import logging
from typing import Optional
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult, ModelProvider
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="Email Scam Detection Agent",
    description="Analyzes email content for phishing, impersonation, urgency, and financial scams."
)
class EmailScamDetectionAgent(BaseSubAgent):
    """Sub-agent specialized in identifying email-based fraud."""

    @property
    def name(self) -> str:
        return "Email Scam Detection Agent"

    @property
    def description(self) -> str:
        return "Analyzes email content for phishing, impersonation, urgency, and financial scams."

    def analyze(self, content: str, model_provider: Optional[ModelProvider] = None) -> AgentResult:
        logger.info(f"Running email analysis on: {content[:40]}...")
        
        # Check if we should use Live Gemini AI
        if model_provider and not getattr(model_provider, "is_mock", True):
            prompt = f"""
            You are the 'Email Scam Detection Agent' in the AI Fraud Shield cybersecurity system.
            Analyze the following email content for phishing, identity impersonation, artificial urgency, fake lotteries, and financial scams.
            
            Email Content to Analyze:
            "{content}"
            
            Evaluate the overall risk_level (LOW, MEDIUM, HIGH, CRITICAL), assign a confidence score (0.0 to 1.0), and list specific findings as detailed bullet points.
            Include the key 'analyzed_length' containing the integer length of the content in the details object.
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
        confidence = 0.85
        
        # Look for phishing / scam markers
        if "inheritance" in content_lower or "prince" in content_lower or "lottery" in content_lower:
            findings.append("Detected classic advance-fee fraud keywords (lottery/inheritance).")
            risk_level = "HIGH"
        if "urgent" in content_lower or "immediate action" in content_lower or "suspend" in content_lower:
            findings.append("Urgency-inducing language identified (often used to force rash decisions).")
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
        if "bank" in content_lower or "verify your password" in content_lower or "login" in content_lower:
            findings.append("Credential phishing risk: requests credentials or links to login portals.")
            risk_level = "HIGH"
        if "gift card" in content_lower or "wire transfer" in content_lower or ("wire" in content_lower and "$" in content_lower) or "send money" in content_lower:
            findings.append("Request for non-reversible payment methods detected (gift cards, wire transfers, or money sends).")
            risk_level = "CRITICAL" if "urgent" in content_lower else "HIGH"

        if not findings:
            findings.append("No obvious email scam markers detected.")
            confidence = 0.70

        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"analyzed_length": len(content)}
        )
