"""Re-exports the abstract base class for ModelProvider.

Allows central access under the llm subpackage structure.
"""

from fraud_shield.interfaces import ModelProvider

__all__ = ["ModelProvider"]
