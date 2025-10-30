"""
Agent Registry for Multi-Agent Report Generation System

This module maintains a central registry of all available agents and provides
utility functions to initialize, retrieve, and list agents.
"""

from typing import Dict

from app.agents.base_agent import BaseAgent
from app.agents.routing_agent import RoutingAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.agents.template_agent import TemplateAgent
from app.agents.user_input_collector import UserInputCollectorAgent


# Global registry to store initialized agent instances
_REGISTER: Dict[str, BaseAgent] = {}


def init_agents() -> None:
    """
    Initialize all agents and register them in the global registry.
    
    This function should be called once during application startup
    (typically in orchestrator.py before building the graph).
    
    Registered agents:
    - routing_agent: Routes requests to appropriate agents
    - template_agent: Handles template discovery and selection
    - user_input_collector: Collects required fields from users
    - scheduling_agent: Schedules and triggers reports
    """
    agents = [
        RoutingAgent(),
        TemplateAgent(),
        UserInputCollectorAgent(),
        SchedulingAgent()
    ]
    
    for agent in agents:
        _REGISTER[agent.name()] = agent
    
    print(f"✅ Initialized {len(_REGISTER)} agents: {list(_REGISTER.keys())}")


def get_agent(name: str) -> BaseAgent:
    """
    Retrieve an agent instance by name.
    
    Args:
        name: The agent's unique identifier (e.g., 'routing_agent')
    
    Returns:
        The corresponding agent instance
    
    Raises:
        KeyError: If the agent name is not found in the registry
    
    Example:
        >>> agent = get_agent("template_agent")
        >>> result = agent.execute(state)
    """
    if name not in _REGISTER:
        available = list(_REGISTER.keys())
        raise KeyError(
            f"Agent '{name}' not found in registry. "
            f"Available agents: {available}"
        )
    
    return _REGISTER[name]


def list_agents() -> list:
    """
    List all registered agent names.
    
    Returns:
        List of agent names currently in the registry
    
    Example:
        >>> list_agents()
        ['routing_agent', 'template_agent', 'user_input_collector', 'scheduling_agent']
    """
    return list(_REGISTER.keys())


def agent_exists(name: str) -> bool:
    """
    Check if an agent is registered.
    
    Args:
        name: The agent name to check
    
    Returns:
        True if agent exists in registry, False otherwise
    
    Example:
        >>> agent_exists("template_agent")
        True
        >>> agent_exists("unknown_agent")
        False
    """
    return name in _REGISTER


def clear_registry() -> None:
    """
    Clear all agents from the registry.
    
    Useful for testing or reinitialization scenarios.
    """
    global _REGISTER
    _REGISTER.clear()
    print("🧹 Agent registry cleared")