"""Custom exceptions for the AI Fraud Shield Coordinator Agent.

Provides domain-specific exceptions to enable clean exception handling
throughout the orchestrator system.
"""

class FraudShieldError(Exception):
    """Base exception for all errors in the AI Fraud Shield Agent package."""
    pass


class ConfigurationError(FraudShieldError):
    """Raised when there is a configuration error (e.g., missing keys, invalid models)."""
    pass


class RoutingError(FraudShieldError):
    """Raised when the router cannot classify the request or find appropriate agents."""
    pass


class AgentExecutionError(FraudShieldError):
    """Raised when a specialized sub-agent fails to analyze the request."""
    pass


class AggregationError(FraudShieldError):
    """Raised when the results aggregator fails to compute the overall risk score."""
    pass
