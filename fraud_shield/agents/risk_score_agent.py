"""Risk Score Sub-Agent.

Compiles individual threat markers, maps vulnerability indices, and performs
statistical consolidation to yield a unified risk rating.
"""

import logging
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="Risk Score Agent",
    description="Compiles threat metrics and consolidates risk parameters for overall profiling."
)
class RiskScoreAgent(BaseSubAgent):
    """Sub-agent specialized in threat scoring and vulnerability metrics."""

    @property
    def name(self) -> str:
        return "Risk Score Agent"

    @property
    def description(self) -> str:
        return "Compiles threat metrics and consolidates risk parameters for overall profiling."

    def analyze(self, content: str) -> AgentResult:
        logger.info(f"Running risk scoring compiler on: {content[:40]}...")
        content_lower = content.lower()
        findings = []
        risk_level = "LOW"
        confidence = 0.92
        
        # Risk Score compiles metadata triggers. It looks for general insecurity indicators.
        threat_count = 0
        if "otp" in content_lower or "one time password" in content_lower:
            threat_count += 3
            findings.append("Identified severe security threat: OTP exposure requested.")
        if "link" in content_lower or "url" in content_lower or "http" in content_lower:
            threat_count += 1
            findings.append("Identified digital link redirection vector.")
        if "urgent" in content_lower or "now" in content_lower or "limit" in content_lower:
            threat_count += 1
            findings.append("Identified psychological pressure indicator (urgency).")
        if "bank" in content_lower or "account" in content_lower or "card" in content_lower:
            threat_count += 2
            findings.append("Identified financial impersonation vector.")
            
        if threat_count >= 5:
            risk_level = "CRITICAL"
        elif threat_count >= 3:
            risk_level = "HIGH"
        elif threat_count >= 1:
            risk_level = "MEDIUM"
            
        if not findings:
            findings.append("Baseline threat level assessed. No immediate threat vectors triggered.")
            confidence = 0.80

        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"threat_score_index": threat_count}
        )
