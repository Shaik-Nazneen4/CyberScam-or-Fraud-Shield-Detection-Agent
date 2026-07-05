"""Internship & Job Scam Detection Sub-Agent.

Analyzes job listings, internship offers, hiring messages, and onboarding procedures
for advance-fee job scams, fake corporate domains, and task-based financial scams.
"""

import logging
from typing import Optional
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult, ModelProvider
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="Internship & Job Scam Detection Agent",
    description="Evaluates job listings and internship offers for advance-fee scams, suspicious recruiting, and tasks scams."
)
class JobScamDetectionAgent(BaseSubAgent):
    """Sub-agent specialized in identifying job and internship scams."""

    @property
    def name(self) -> str:
        return "Internship & Job Scam Detection Agent"

    @property
    def description(self) -> str:
        return "Evaluates job listings and internship offers for advance-fee scams, suspicious recruiting, and tasks scams."

    def analyze(self, content: str, model_provider: Optional[ModelProvider] = None) -> AgentResult:
        logger.info(f"Running job/internship analysis on: {content[:40]}...")

        # Check if we should use Live Gemini AI
        if model_provider and not getattr(model_provider, "is_mock", True):
            prompt = f"""
            You are the 'Internship & Job Scam Detection Agent' in the AI Fraud Shield cybersecurity system.
            Analyze the following text for advance-fee job scams, fraudulent internship offers, suspicious recruiting channels, and task-based financial fraud.

            Content to Analyze:
            "{content}"

            Evaluate the overall risk_level (LOW, MEDIUM, HIGH, CRITICAL), assign a confidence score (0.0 to 1.0), and list specific findings as detailed bullet points.
            Include the key 'is_job_intent' with a boolean value in the details object.
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
        confidence = 0.86
        
        # Check job scam indicators
        if "telegram" in content_lower or "whatsapp" in content_lower:
            if "interview" in content_lower or "recruit" in content_lower:
                findings.append("Recruitment process conducted entirely on personal chat apps (Telegram/WhatsApp), which is highly unprofessional and indicates a scam.")
                risk_level = "HIGH"
                
        if "pay" in content_lower or "salary" in content_lower or "earn" in content_lower:
            if "quick" in content_lower or "easy" in content_lower or "no experience" in content_lower:
                findings.append("High compensation promised for low-skill, low-effort work (e.g. 'earn $500/day clicking links').")
                risk_level = "HIGH"
                
        if "deposit" in content_lower or "pay for training" in content_lower or "buy equipment" in content_lower:
            findings.append("Advance-fee job scam: demands payment for training materials, background checks, or startup equipment.")
            risk_level = "CRITICAL"

        if not findings:
            findings.append("No obvious internship or job scam patterns detected.")
            confidence = 0.70

        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"is_job_intent": True}
        )
