"""Routing and classification component for the Coordinator Agent.

Determines the nature of the user input and maps it to the list of specialized
sub-agents that should be executed to resolve the request.
"""

import logging
from typing import List
from pydantic import BaseModel, Field
from fraud_shield.interfaces import ModelProvider
from fraud_shield.registry import AgentRegistry
from fraud_shield.exceptions import RoutingError

logger = logging.getLogger(__name__)

class RoutingDecision(BaseModel):
    """Structured routing decision schema returned by the classifier."""
    input_type: str = Field(..., description="The type of scam/fraud query (e.g. email, sms_whatsapp, url, shopping, job_internship, general_banking, multi_risk_report).")
    selected_agents: List[str] = Field(..., description="List of sub-agent names to execute.")


class RequestRouter:
    """Orchestrates query classification and routes tasks to registered sub-agents."""

    def __init__(self, model_provider: ModelProvider):
        """Initializes the router with a model provider (strategy pattern)."""
        self.model_provider = model_provider

    def route(self, content: str) -> RoutingDecision:
        """Classifies the content and decides which registered agents to trigger.
        
        Args:
            content: The raw user message.
            
        Returns:
            A RoutingDecision object.
            
        Raises:
            RoutingError: If classification fails or selects no valid agents.
        """
        logger.info("Routing user request...")
        
        # Retrieve currently registered agents and descriptions to inject into prompt context
        registered_agents = AgentRegistry.get_agent_metadata()
        agent_names = AgentRegistry.get_registered_names()
        
        if not agent_names:
            raise RoutingError("No sub-agents are registered in the system registry.")
            
        # Build prompt for LLM structure
        agents_context = "\n".join([
            f"- Name: {meta['name']}\n  Description: {meta['description']}"
            for meta in registered_agents
        ])
        
        prompt = f"""
You are the Routing & Classification component of a cybersecurity Multi-Agent System called AI Fraud Shield.
Your job is to analyze the user input, classify its category, and select the appropriate specialized sub-agents to invoke.

Available Agents:
{agents_context}

Supported Categories:
- email (Email scam/phishing analysis)
- sms_whatsapp (Smishing, WhatsApp hijacking, messaging fraud)
- url (Suspicious links/domains/redirects analysis)
- shopping (Fake online stores, counterfeit sellers, deal trust)
- job_internship (Job recruiting fraud, task scams, work-from-home fraud)
- general_banking (OTP requests, bank impersonation phone calls)
- multi_risk_report (User requests complete check of multiple threat vectors, or 'analyze everything')
- general_query (None of the above match, fallback to general advice)

User Input: "{content}"

Instructions:
1. Classify the input_type into one of the Supported Categories above.
2. Select one or more relevant sub-agents from the list of Available Agents. For requests asking to analyze everything or general security checkups, select multiple agents.
3. Output the result strictly in JSON matching the requested RoutingDecision schema.
"""

        try:
            decision: RoutingDecision = self.model_provider.generate_json(prompt, RoutingDecision)
            
            # Validate that the model selected registered agents
            valid_agents = []
            for agent_name in decision.selected_agents:
                if agent_name in agent_names:
                    valid_agents.append(agent_name)
                else:
                    logger.warning(f"Router LLM selected non-registered agent: '{agent_name}'. Ignoring.")
                    
            if not valid_agents:
                logger.warning("Router LLM did not select any valid registered agents. Falling back to default list.")
                # Sensible defaults based on input_type
                if decision.input_type == "email":
                    valid_agents = ["Email Scam Detection Agent"]
                elif decision.input_type == "sms_whatsapp":
                    valid_agents = ["SMS & WhatsApp Scam Detection Agent"]
                elif decision.input_type == "url":
                    valid_agents = ["URL Analysis Agent"]
                elif decision.input_type == "shopping":
                    valid_agents = ["Shopping Trust Agent"]
                elif decision.input_type == "job_internship":
                    valid_agents = ["Internship & Job Scam Detection Agent"]
                else:
                    # Fallback to Risk Score and Safety Advisor for general/banking
                    valid_agents = [name for name in ["Risk Score Agent", "Safety Advisor Agent"] if name in agent_names]
                    
            decision.selected_agents = valid_agents
            logger.info(f"Routing Decision: Input Type: {decision.input_type}, Agents: {decision.selected_agents}")
            return decision
            
        except Exception as e:
            logger.error(f"Failed to route request: {str(e)}")
            raise RoutingError(f"Error occurred during query classification and routing: {str(e)}") from e
