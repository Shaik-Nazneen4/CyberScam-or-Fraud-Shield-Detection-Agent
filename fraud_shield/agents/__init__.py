"""Sub-agents package for AI Fraud Shield.

Imports and registers all specialized sub-agents with the dynamic registry.
"""

from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.agents.email_agent import EmailScamDetectionAgent
from fraud_shield.agents.sms_whatsapp_agent import SmsWhatsAppScamDetectionAgent
from fraud_shield.agents.url_agent import UrlAnalysisAgent
from fraud_shield.agents.shopping_agent import ShoppingTrustAgent
from fraud_shield.agents.job_agent import JobScamDetectionAgent
from fraud_shield.agents.risk_score_agent import RiskScoreAgent
from fraud_shield.agents.safety_advisor_agent import SafetyAdvisorAgent

__all__ = [
    "BaseSubAgent",
    "EmailScamDetectionAgent",
    "SmsWhatsAppScamDetectionAgent",
    "UrlAnalysisAgent",
    "ShoppingTrustAgent",
    "JobScamDetectionAgent",
    "RiskScoreAgent",
    "SafetyAdvisorAgent",
]
