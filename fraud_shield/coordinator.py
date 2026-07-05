"""Central coordinator (orchestrator) for the AI Fraud Shield Multi-Agent System.

Manages the lifecycle of a request: classification, routing to specialized
sub-agents, error handling/containment, and output aggregation.
Exposes standard Python methods and an ADK-compatible wrapper.
"""

import logging
from typing import Optional, Dict, List
import google.adk

from fraud_shield.interfaces import ModelProvider, CoordinatorResponse, AgentResult
import fraud_shield.agents  # Trigger sub-agent dynamic registration
from fraud_shield.llm.mock_provider import MockModelProvider
from fraud_shield.registry import AgentRegistry
from fraud_shield.router import RequestRouter, RoutingDecision
from fraud_shield.aggregator import ResultAggregator
from fraud_shield.exceptions import FraudShieldError, RoutingError, AgentExecutionError

logger = logging.getLogger(__name__)

class CoordinatorAgent:
    """The central Coordinator Agent of the AI Fraud Shield system.
    
    Coordinates the routing, execution, and aggregation phases of the pipeline.
    Uses dependency injection for its LLM provider, keeping it independent of
    specific Gemini client library requirements.
    """

    def __init__(
        self,
        model_provider: Optional[ModelProvider] = None,
        router: Optional[RequestRouter] = None,
        aggregator: Optional[ResultAggregator] = None
    ):
        """Initializes the coordinator with its core modules.
        
        Args:
            model_provider: Implementation of ModelProvider. Defaults to MockModelProvider.
            router: RequestRouter instance. If None, one is created automatically.
            aggregator: ResultAggregator instance. If None, one is created automatically.
        """
        self.model_provider = model_provider or MockModelProvider()
        self.router = router or RequestRouter(self.model_provider)
        self.aggregator = aggregator or ResultAggregator()
        logger.info("CoordinatorAgent successfully initialized.")

    def process_request(
        self,
        content: str,
        selected_agents: Optional[List[str]] = None
    ) -> CoordinatorResponse:
        """Processes a scam detection query through the orchestration pipeline.
        
        This is the primary Python execution entry point. It contains robust
        exception handling to ensure sub-agent failures do not crash the entire system.
        
        Args:
            content: The text query or message provided by the user.
            selected_agents: Optional list of sub-agent names to execute, bypassing routing.
            
        Returns:
            A CoordinatorResponse containing structured analysis and advice.
        """
        logger.info(f"Processing request: '{content[:50]}...'")
        
        if not content or not content.strip():
            logger.warning("Empty request content received.")
            return CoordinatorResponse(
                input_type="empty",
                selected_agents=[],
                analysis_status="failed",
                overall_risk="LOW",
                recommendation="Empty request. Please provide content to analyze.",
                next_steps=["Enter email text, message logs, job offers, or website links to analyze."]
            )

        # Phase 1: Classification & Routing
        try:
            if selected_agents is not None:
                # Classify category using router or fallback, but override agents
                try:
                    routing_decision = self.router.route(content)
                    routing_decision.selected_agents = selected_agents
                except Exception:
                    routing_decision = RoutingDecision(
                        input_type="custom_query",
                        selected_agents=selected_agents
                    )
            else:
                routing_decision = self.router.route(content)
        except RoutingError as e:
            logger.error(f"Routing phase failed: {str(e)}")
            return CoordinatorResponse(
                input_type="unknown",
                selected_agents=[],
                analysis_status="failed",
                overall_risk="MEDIUM",
                recommendation="Unable to classify request or select agents due to an internal routing failure.",
                next_steps=["Try rephrasing your request.", "Contact system administrator if the issue persists."]
            )

        # Phase 2: Dynamic Execution
        results: Dict[str, AgentResult] = {}
        failures: List[str] = []

        for agent_name in routing_decision.selected_agents:
            logger.info(f"Delegating task to sub-agent: {agent_name}")
            sub_agent = AgentRegistry.get_agent(agent_name)
            
            if not sub_agent:
                logger.error(f"Selected agent '{agent_name}' was not found in registry.")
                failures.append(agent_name)
                continue

            try:
                # Execute agent analysis
                # In a production environment, this could be run asynchronously in parallel
                result: AgentResult = sub_agent.analyze(content)
                results[agent_name] = result
                logger.info(f"Sub-agent '{agent_name}' completed. Evaluated risk: {result.risk_level}")
            except Exception as e:
                logger.error(f"Error during execution of sub-agent '{agent_name}': {str(e)}", exc_info=True)
                failures.append(agent_name)

        # Phase 3: Aggregation
        try:
            response: CoordinatorResponse = self.aggregator.aggregate(
                input_type=routing_decision.input_type,
                selected_agents=routing_decision.selected_agents,
                results=results,
                failures=failures
            )
            logger.info(f"Orchestration completed successfully. Overall Risk: {response.overall_risk}")
            return response
        except Exception as e:
            logger.error(f"Aggregation phase failed: {str(e)}", exc_info=True)
            return CoordinatorResponse(
                input_type=routing_decision.input_type,
                selected_agents=routing_decision.selected_agents,
                analysis_status="failed",
                overall_risk="HIGH",
                recommendation="An error occurred while compiling analysis results. Treat request with caution.",
                next_steps=["Assume high risk and do not interact with suspicious items."]
            )

    def as_adk_agent(self) -> google.adk.Agent:
        """Wraps the CoordinatorAgent into a standard google.adk.Agent instance.
        
        This enables deployment into the Google Enterprise Agent platform or running
        via the ADK runner environment.
        
        Returns:
            An instantiated google.adk.Agent with this coordinator set as a tool.
        """
        
        def analyze_fraud_shield_request(user_query: str) -> str:
            """Main entry tool for AI Fraud Shield. Analyzes potential scam/fraud queries and yields a structured JSON report."""
            response = self.process_request(user_query)
            return response.model_dump_json(indent=2)
            
        return google.adk.Agent(
            name="AI_Fraud_Shield_Coordinator",
            description=(
                "Orchestrates specialized sub-agents to detect email scams, "
                "WhatsApp smishing, URL trust, job scams, and compile consolidated safety risk assessments."
            ),
            instruction=(
                "You are the AI Fraud Shield Coordinator Agent. You serve as the central gateway "
                "of the multi-agent system. When a user submits an email, SMS, message, link, "
                "or job offer for verification, you must call the `analyze_fraud_shield_request` tool "
                "with the exact user query. Return the structured JSON response as is."
            ),
            tools=[analyze_fraud_shield_request],
            output_schema=CoordinatorResponse
        )
