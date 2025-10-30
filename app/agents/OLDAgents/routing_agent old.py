from typing import Dict, Any

from app.agents.base_agent import BaseAgent
from app.llm import llm_complete


class RoutingAgent(BaseAgent):

    def name(self) -> str:
        return "routing_agent"

    def system_prompt(self) -> str:
        return """
            You are an intelligent router.
            "Classify the user intent based on their message  and decide which agent should pick"
            Available agent:
            - template_agent: Handles template selection, browsing templates, choosing report types.
            - scheduling_agent: Handle scheduling report based on the template selected by the user, view reports.
            Return only: template_agent or scheduling_agent
        """

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
            {self.system_prompt()}
            User: {state['user_message']}
        """

        # template_agent
        decision = llm_complete(prompt).split()[0].strip().lower()
        if decision not in {"template_agent" , "scheduling_agent"}:
            decision = "template_agent" # Unknown so we can redirect to this node to reply that we can't full fill your request

        state["next_agent"] = decision
        state["reply"] = f"Routing to: {decision}"

