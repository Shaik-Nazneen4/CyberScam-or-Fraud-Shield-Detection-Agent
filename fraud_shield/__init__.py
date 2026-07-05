"""AI Fraud Shield Agent package.

This package provides the core modules for classifying user requests,
orchestrating specialized scam detection sub-agents, and aggregating results.
"""

from fraud_shield.coordinator import CoordinatorAgent
from fraud_shield.interfaces import CoordinatorResponse, AgentResult

__all__ = ["CoordinatorAgent", "CoordinatorResponse", "AgentResult"]
