"""Unit tests for the AI Fraud Shield Coordinator Agent.

Tests routing, agent registry, error containment (failures), and result aggregation.
"""

import pytest
from typing import Dict

from fraud_shield.coordinator import CoordinatorAgent
from fraud_shield.interfaces import BaseSubAgent, AgentResult
from fraud_shield.registry import AgentRegistry
from fraud_shield.exceptions import RoutingError
from fraud_shield.router import RequestRouter, RoutingDecision
from fraud_shield.llm.mock_provider import MockModelProvider

# --- Mock classes for custom testing scenarios ---

class MockSucceedingAgent(BaseSubAgent):
    @property
    def name(self) -> str:
        return "Succeeding Test Agent"
        
    @property
    def description(self) -> str:
        return "Always succeeds with high risk."
        
    def analyze(self, content: str) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            risk_level="HIGH",
            confidence=0.99,
            findings=["Test finding from succeeding agent."],
            details={}
        )

class MockFailingAgent(BaseSubAgent):
    @property
    def name(self) -> str:
        return "Failing Test Agent"
        
    @property
    def description(self) -> str:
        return "Always throws an exception."
        
    def analyze(self, content: str) -> AgentResult:
        raise ValueError("Simulated sub-agent failure.")


@pytest.fixture(autouse=True)
def clean_registry_sandbox():
    """Fixture to backup and restore the AgentRegistry state between tests.
    
    Ensures tests are completely hermetic and isolated from registry changes.
    """
    backup_registry = dict(AgentRegistry._registry)
    backup_descriptions = dict(AgentRegistry._descriptions)
    backup_instances = dict(AgentRegistry._instances)
    yield
    AgentRegistry._registry = backup_registry
    AgentRegistry._descriptions = backup_descriptions
    AgentRegistry._instances = backup_instances


def test_registry_registration():
    """Verify that agents can be registered and retrieved correctly."""
    # Register agents using registry methods directly or decorators
    AgentRegistry.register("Succeeding Test Agent", "Always succeeds with high risk.")(MockSucceedingAgent)
    AgentRegistry.register("Failing Test Agent", "Always throws an exception.")(MockFailingAgent)
    
    assert "Succeeding Test Agent" in AgentRegistry.get_registered_names()
    assert "Failing Test Agent" in AgentRegistry.get_registered_names()
    
    agent = AgentRegistry.get_agent("Succeeding Test Agent")
    assert isinstance(agent, MockSucceedingAgent)


def test_routing_decisions():
    """Verify that router maps keywords to appropriate category and agents."""
    model_provider = MockModelProvider()
    router = RequestRouter(model_provider)
    
    # 1. Test WhatsApp Smishing message routing
    decision = router.route("Is this WhatsApp message a scam? OTP validation required.")
    assert decision.input_type == "sms_whatsapp"
    assert "SMS & WhatsApp Scam Detection Agent" in decision.selected_agents
    
    # 2. Test Email Scam routing
    decision = router.route("I won a lottery email from a prince.")
    assert decision.input_type == "email"
    assert "Email Scam Detection Agent" in decision.selected_agents
    
    # 3. Test Job Scam routing
    decision = router.route("Genuine internship offer Telegram task.")
    assert decision.input_type == "job_internship"
    assert "Internship & Job Scam Detection Agent" in decision.selected_agents


def test_coordinator_success_flow():
    """Verify the end-to-end coordinator flow when agents run successfully."""
    # Clean registry and add our test agent
    AgentRegistry.clear()
    AgentRegistry.register("Succeeding Test Agent", "Succeeds")(MockSucceedingAgent)
    
    # Mock router to select our succeeding agent
    class CustomRouter(RequestRouter):
        def route(self, content: str) -> RoutingDecision:
            return RoutingDecision(
                input_type="test_type",
                selected_agents=["Succeeding Test Agent"]
            )
            
    coordinator = CoordinatorAgent(router=CustomRouter(MockModelProvider()))
    response = coordinator.process_request("Analyze this test prompt.")
    
    assert response.input_type == "test_type"
    assert response.selected_agents == ["Succeeding Test Agent"]
    assert response.analysis_status == "success"
    assert response.overall_risk == "HIGH"
    assert "Test finding from succeeding agent." in response.recommendation


def test_coordinator_error_containment():
    """Verify that a failing agent does not crash the coordinator, and yields partial_success."""
    AgentRegistry.clear()
    AgentRegistry.register("Succeeding Test Agent", "Succeeds")(MockSucceedingAgent)
    AgentRegistry.register("Failing Test Agent", "Fails")(MockFailingAgent)
    
    # Mock router to select both agents
    class CustomRouter(RequestRouter):
        def route(self, content: str) -> RoutingDecision:
            return RoutingDecision(
                input_type="test_type",
                selected_agents=["Succeeding Test Agent", "Failing Test Agent"]
            )
            
    coordinator = CoordinatorAgent(router=CustomRouter(MockModelProvider()))
    response = coordinator.process_request("Analyze this test prompt.")
    
    # Succeeded agent risk level is HIGH. Failing agent failed.
    # Status should be partial_success, overall risk remains HIGH from the successful one.
    assert response.analysis_status == "partial_success"
    assert response.overall_risk == "HIGH"
    assert any("Failing Test Agent" in step for step in response.next_steps)
    assert "Succeeding Test Agent" in response.selected_agents
    assert "Failing Test Agent" in response.selected_agents


def test_coordinator_total_failure():
    """Verify that if all agents fail, the coordinator returns failed status gracefully."""
    AgentRegistry.clear()
    AgentRegistry.register("Failing Test Agent", "Fails")(MockFailingAgent)
    
    class CustomRouter(RequestRouter):
        def route(self, content: str) -> RoutingDecision:
            return RoutingDecision(
                input_type="test_type",
                selected_agents=["Failing Test Agent"]
            )
            
    coordinator = CoordinatorAgent(router=CustomRouter(MockModelProvider()))
    response = coordinator.process_request("Analyze this test prompt.")
    
    assert response.analysis_status == "failed"
    assert response.overall_risk == "HIGH"  # Default fallback overall risk on error
    assert "An error occurred while compiling analysis results" in response.recommendation


def test_coordinator_manual_agent_override():
    """Verify that passing selected_agents directly bypasses the router and runs only those agents."""
    AgentRegistry.clear()
    AgentRegistry.register("Succeeding Test Agent", "Succeeds")(MockSucceedingAgent)
    AgentRegistry.register("Failing Test Agent", "Fails")(MockFailingAgent)

    # Router would normally pick "Failing Test Agent" for any input, but we override it
    class AlwaysFailRouter(RequestRouter):
        def route(self, content: str) -> RoutingDecision:
            return RoutingDecision(
                input_type="test_type",
                selected_agents=["Failing Test Agent"]
            )

    coordinator = CoordinatorAgent(router=AlwaysFailRouter(MockModelProvider()))

    # Override: run only the succeeding agent regardless of what the router would choose
    response = coordinator.process_request(
        "Analyze this test prompt.",
        selected_agents=["Succeeding Test Agent"]
    )

    # The succeeding agent ran, not the failing one
    assert response.analysis_status == "success"
    assert response.overall_risk == "HIGH"
    assert "Succeeding Test Agent" in response.selected_agents
    assert "Failing Test Agent" not in response.selected_agents
    # The override should still determine the input_type via the router (test_type)
    assert response.input_type in ("test_type", "custom_query")
