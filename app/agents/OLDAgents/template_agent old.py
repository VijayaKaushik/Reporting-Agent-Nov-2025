from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from ..tools.fetch_template import fetch_template_tool, describe_template_tool


class TemplateAgent(BaseAgent):
    def name(self) -> str:
        return "template_agent"

    def system_prompt(self) -> str:
        return """
            "You are Template Agent"
            "You help user find and select the best template for selecting template"
            You can:
            "-- User 'fetch_template_tool' to get list of template"
            "-- User 'describe_template_tool' to describe a selected template."
        """

    def tools(self):
        return [fetch_template_tool, describe_template_tool]