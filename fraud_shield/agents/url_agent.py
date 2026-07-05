"""URL Analysis Sub-Agent.

Analyzes domain characteristics, URL structure, and suspicious redirect links
to detect phishing pages, malware downloads, and copycat websites.
"""

import logging
import re
from typing import Optional
from fraud_shield.agents.base import BaseSubAgent
from fraud_shield.interfaces import AgentResult, ModelProvider
from fraud_shield.registry import AgentRegistry

logger = logging.getLogger(__name__)

@AgentRegistry.register(
    name="URL Analysis Agent",
    description="Analyzes URLs and links for typosquatting, suspicious domains, and redirect risks."
)
class UrlAnalysisAgent(BaseSubAgent):
    """Sub-agent specialized in link analysis."""

    @property
    def name(self) -> str:
        return "URL Analysis Agent"

    @property
    def description(self) -> str:
        return "Analyzes URLs and links for typosquatting, suspicious domains, and redirect risks."

    def analyze(self, content: str, model_provider: Optional[ModelProvider] = None) -> AgentResult:
        logger.info(f"Running URL analysis on: {content[:40]}...")
        
        # Extract links first to count them
        urls = re.findall(r'(https?://[^\s]+)', content)
        
        # Check if we should use Live Gemini AI
        if model_provider and not getattr(model_provider, "is_mock", True):
            prompt = f"""
            You are the 'URL Analysis Agent' in the AI Fraud Shield cybersecurity system.
            Analyze the following text content for suspicious links, domain name typosquatting, lookalike domains (e.g. goog1e), URL shorteners, or malicious URL query parameters.
            
            Content to Analyze:
            "{content}"
            
            Evaluate the overall risk_level (LOW, MEDIUM, HIGH, CRITICAL), assign a confidence score (0.0 to 1.0), and list specific findings as detailed bullet points.
            Include the key 'detected_urls_count' with the integer count of URLs found in the details object.
            Output strictly in JSON matching the requested AgentResult schema.
            """
            try:
                return model_provider.generate_json(prompt, AgentResult)
            except Exception as e:
                logger.error(f"Gemini live analysis failed for {self.name}: {e}. Falling back to rule-based analysis.")

        # Fallback to local rule-based matching
        findings = []
        risk_level = "LOW"
        confidence = 0.88
        
        for url in urls:
            url_lower = url.lower()
            if "bit.ly" in url_lower or "tinyurl" in url_lower or "t.co" in url_lower:
                findings.append(f"Identified URL shortener ({url}), obfuscating destination.")
                risk_level = "MEDIUM"
            if "login" in url_lower or "verify" in url_lower or "secure" in url_lower:
                findings.append(f"Suspicious path keyword in URL: '{url}'. Contains high-risk identity keywords.")
                risk_level = "HIGH"
            # Typosquatting / domain impersonation checks (mock)
            if "goog1e" in url_lower or "amazon-security" in url_lower or "paypal-update" in url_lower or "secure-bank" in url_lower:
                findings.append(f"High risk of domain impersonation/typosquatting: '{url}'.")
                risk_level = "CRITICAL"
                
        if not urls:
            findings.append("No explicit HTTP/HTTPS links found in the text.")
            # Check if user claims to want a URL checked but didn't write it properly
            if "url" in content.lower() or "link" in content.lower() or "website" in content.lower():
                findings.append("Context mentions checking a URL, but no valid URL format was found.")
                risk_level = "MEDIUM"
                confidence = 0.60
            else:
                confidence = 0.70

        return AgentResult(
            agent_name=self.name,
            risk_level=risk_level,
            confidence=confidence,
            findings=findings,
            details={"detected_urls_count": len(urls)}
        )
