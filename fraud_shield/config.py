"""Configuration settings for the AI Fraud Shield Coordinator Agent.

Provides centralized configuration for models, logs, registry details, and flags.
"""

import logging
import os
from typing import Dict, Any

# Model Configuration
# We allow environment override for the model name, defaulting to gemini-2.5-flash
DEFAULT_MODEL_NAME = os.getenv("FRAUD_SHIELD_MODEL", "gemini-2.5-flash")

# Logging Configuration
LOG_LEVEL_NAME = os.getenv("FRAUD_SHIELD_LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME.upper(), logging.INFO)

# Config structure for logging setup
LOGGING_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

def setup_logging() -> None:
    """Configures system-wide logging for the AI Fraud Shield application."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOGGING_FORMAT,
        handlers=[
            logging.StreamHandler()
        ]
    )
    # Reduce noise from external modules if necessary
    logging.getLogger("google").setLevel(logging.WARNING)

# Risk Thresholds and Aggregation Configuration
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Mapping of risk string representation to numeric value for logical aggregation
RISK_MAPPING = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

NUMERIC_TO_RISK = {v: k for k, v in RISK_MAPPING.items()}
