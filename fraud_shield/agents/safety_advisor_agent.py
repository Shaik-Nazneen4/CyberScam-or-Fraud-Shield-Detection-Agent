"""Safety Advisor Sub-Agent.

Generates educational safety tips and protective instructions based on the
classified request vector.
"""

import logging
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="Safety Advisor Agent",
    description="Provides security safety recommendations and educational advisory next steps."
)
class SafetyAdvisorAgent(BaseSubAgent):
    """Sub-agent specialized in safety advising and cyber-hygiene next steps."""

    @property
    def name(self) -> str:
        return "Safety Advisor Agent"

    @property
    def description(self) -> str:
        return "Provides security safety recommendations and educational advisory next steps."

    def analyze(self, content: str) -> AgentResult:
        logger.info(f"Running safety advisor on: {content[:40]}...")
        content_lower = content.lower()
        findings = []
        risk_level = "LOW"
        confidence = 0.95
        
        # Determine safety instructions based on keywords
        if "otp" in content_lower or "bank" in content_lower or "call" in content_lower:
            findings.append("Advisory: Banks and official agencies NEVER call to request your OTP or login passwords.")
            findings.append("Advisory: If you suspect a call is fraudulent, hang up and dial the official number printed on your card.")
            risk_level = "HIGH"
        elif "url" in content_lower or "link" in content_lower or "website" in content_lower:
            findings.append("Advisory: Avoid clicking on links in unsolicited messages or emails.")
            findings.append("Advisory: Always check for HTTPS and confirm the exact domain name before entering credentials.")
            risk_level = "MEDIUM"
        elif "job" in content_lower or "internship" in content_lower:
            findings.append("Advisory: Never pay upfront fees to secure a job or internship.")
            findings.append("Advisory: Professional organizations do not recruit or conduct interviews solely on Telegram or WhatsApp.")
            risk_level = "MEDIUM"
        else:
            findings.append("Advisory: Stay vigilant against social engineering and suspicious requests for personal information.")
            
        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"advisory_items_count": len(findings)}
        )
