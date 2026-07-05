"""Abstract interfaces and structured data models for the AI Fraud Shield Agent.

Defines Pydantic models for inputs and outputs, as well as abstract base classes
for LLM providers and specialized sub-agents.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

# --- Data Models (Pydantic schemas) ---

class AgentResult(BaseModel):
    """Structured output returned by each specialized sub-agent."""
    agent_name: str = Field(..., description="The unique name of the sub-agent.")
    risk_level: str = Field(..., description="The risk level evaluated: LOW, MEDIUM, HIGH, CRITICAL.")
    confidence: float = Field(..., description="The confidence score of the evaluation (0.0 to 1.0).")
    findings: List[str] = Field(default_factory=list, description="Key bullet points detailing the findings.")
    details: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary sub-agent specific metadata.")


class CoordinatorResponse(BaseModel):
    """The final structured response returned by the Coordinator Agent to the user."""
    input_type: str = Field(..., description="Classified type of user input (e.g., email, sms_whatsapp, url, shopping, job_internship, general_banking, multi_risk_report).")
    selected_agents: List[str] = Field(..., description="Specialized agents invoked to process this request.")
    analysis_status: str = Field(..., description="Status of the analysis (e.g., success, partial_success, failed).")
    overall_risk: str = Field(..., description="Consolidated overall risk level (LOW, MEDIUM, HIGH, CRITICAL).")
    recommendation: str = Field(..., description="Primary advisory recommendation for the user.")
    next_steps: List[str] = Field(..., description="Actionable next steps the user should take to stay safe.")
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict, description="Detailed results from each sub-agent.")


# --- Abstract Base Classes ---

class ModelProvider(ABC):
    """Abstract interface for large language model interactions.
    
    Ensures the Coordinator remains independent of specific Gemini/Vertex implementation details.
    """
    
    @abstractmethod
    def generate_json(self, prompt: str, response_schema: Type[T]) -> T:
        """Query the model to get structured JSON output matching the Pydantic schema."""
        pass
        
    @abstractmethod
    def classify(self, content: str, categories: List[str]) -> str:
        """Classify a piece of text into one of the specified categories."""
        pass


class BaseSubAgent(ABC):
    """Abstract interface that all specialized sub-agents must inherit from."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The formal name of the sub-agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what this sub-agent analyzes."""
        pass

    @abstractmethod
    def analyze(self, content: str, model_provider: Optional[ModelProvider] = None) -> AgentResult:
        """Performs the scam/fraud detection analysis on the provided content.
        
        Args:
            content: The text input from the user.
            model_provider: Optional ModelProvider to run live LLM analysis.
            
        Returns:
            An AgentResult detailing the risk level, confidence, and specific findings.
        """
        pass
