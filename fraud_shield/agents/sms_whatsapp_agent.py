"""SMS & WhatsApp Scam Detection Sub-Agent.

Analyzes text/messages for smishing, WhatsApp hijacking patterns, support impersonations,
and verification code (OTP) harvesting.
"""

import logging
from typing import Optional
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult, ModelProvider
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="SMS & WhatsApp Scam Detection Agent",
    description="Analyzes SMS and WhatsApp messages for smishing, verification requests, and account hijacking flags."
)
class SmsWhatsAppScamDetectionAgent(BaseSubAgent):
    """Sub-agent specialized in identifying mobile messaging scams."""

    @property
    def name(self) -> str:
        return "SMS & WhatsApp Scam Detection Agent"

    @property
    def description(self) -> str:
        return "Analyzes SMS and WhatsApp messages for smishing, verification requests, and account hijacking flags."

    def analyze(self, content: str, model_provider: Optional[ModelProvider] = None) -> AgentResult:
        logger.info(f"Running SMS/WhatsApp analysis on: {content[:40]}...")
        
        # Check if we should use Live Gemini AI
        if model_provider and not getattr(model_provider, "is_mock", True):
            prompt = f"""
            You are the 'SMS & WhatsApp Scam Detection Agent' in the AI Fraud Shield cybersecurity system.
            Analyze the following text or chat message for smishing, verification code harvesting (OTP requests), account takeover or hijacking signs, and support/family impersonation.
            
            Message Content to Analyze:
            "{content}"
            
            Evaluate the overall risk_level (LOW, MEDIUM, HIGH, CRITICAL), assign a confidence score (0.0 to 1.0), and list specific findings as detailed bullet points.
            Include the key 'contains_otp_request' with a boolean value in the details object.
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
        confidence = 0.90
        
        # Look for smishing/hijacking indicators
        if "otp" in content_lower or "one time password" in content_lower or "verification code" in content_lower:
            findings.append("Critical threat: Request for One-Time Password (OTP) or Verification Code detected.")
            risk_level = "CRITICAL"
        if "bank called" in content_lower or "security alert" in content_lower or "unusual login" in content_lower:
            findings.append("Bank impersonation / social engineering tactics identified.")
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
        if "click here to verify" in content_lower or "wa.me" in content_lower:
            findings.append("Suspicious messaging redirect link detected.")
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
        if "family in need" in content_lower or "accident" in content_lower or "mom" in content_lower:
            findings.append("Potential emergency/family-impersonation scam pattern.")
            risk_level = "HIGH"

        if not findings:
            findings.append("No common SMS or WhatsApp threat indicators identified.")
            confidence = 0.65

        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"contains_otp_request": "otp" in content_lower}
        )
