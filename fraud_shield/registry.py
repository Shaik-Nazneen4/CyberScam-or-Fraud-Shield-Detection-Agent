"""Dynamic registry for specialized scam detection sub-agents.

Allows sub-agents to self-register by decorating their classes. The coordinator
can then query the registry to resolve and instantiate sub-agents dynamically.
"""

import logging
from typing import Dict, Type, List, Optional
from fraud_shield.interfaces import BaseSubAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry class to manage specialized sub-agents."""
    
    _registry: Dict[str, Type[BaseSubAgent]] = {}
    _descriptions: Dict[str, str] = {}
    _instances: Dict[str, BaseSubAgent] = {}

    @classmethod
    def register(cls, name: str, description: str):
        """Decorator to register a sub-agent class.
        
        Args:
            name: The unique string identifier for the sub-agent.
            description: A short explanation of what the sub-agent does.
        """
        def decorator(subclass: Type[BaseSubAgent]):
            if name in cls._registry:
                logger.warning(f"Overwriting already registered agent: {name}")
            cls._registry[name] = subclass
            cls._descriptions[name] = description
            logger.debug(f"Registered agent class '{name}': {subclass.__name__}")
            return subclass
        return decorator

    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseSubAgent]:
        """Gets or instantiates a registered sub-agent by its name.
        
        Args:
            name: The registered name of the sub-agent.
            
        Returns:
            An instance of the sub-agent, or None if not registered.
        """
        if name not in cls._registry:
            logger.error(f"Agent '{name}' is not registered.")
            return None
            
        if name not in cls._instances:
            logger.debug(f"Instantiating sub-agent: {name}")
            agent_class = cls._registry[name]
            cls._instances[name] = agent_class()
            
        return cls._instances[name]

    @classmethod
    def get_registered_names(cls) -> List[str]:
        """Returns a list of all registered sub-agent names."""
        return list(cls._registry.keys())

    @classmethod
    def get_agent_metadata(cls) -> List[Dict[str, str]]:
        """Returns a list of dictionaries with name and description for all agents."""
        return [
            {"name": name, "description": desc}
            for name, desc in cls._descriptions.items()
        ]
        
    @classmethod
    def clear(cls) -> None:
        """Clears the instanced cache and all registrations (useful for testing)."""
        cls._registry.clear()
        cls._descriptions.clear()
        cls._instances.clear()
