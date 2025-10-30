from typing import Dict

from app.agents.base_agent import BaseAgent
from app.agents.routing_agent import RoutingAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.agents.template_agent import TemplateAgent

_REGISTER: Dict[str, BaseAgent] = {}

"""
{
    "template_phase": TemplateAgent()
}
"""

def init_agents():
    for agent in [TemplateAgent(), RoutingAgent(), SchedulingAgent()]:
        _REGISTER[agent.name()] = agent

def get_agent(name: str) -> BaseAgent:
    return _REGISTER[name]

def list_agent():
    return list(_REGISTER.keys()) # ["template_phase"]