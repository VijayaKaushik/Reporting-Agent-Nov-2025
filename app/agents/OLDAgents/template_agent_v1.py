from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
# from ..llm import llm_complete
from ...tools.fetch_template import fetch_template_tool


class TemplateAgentV1(BaseAgent):
    def name(self) -> str:
        return "template_phase"

    def system_prompt(self) -> str:
        return """
            "You help pick the best template. Given user request and list of templates "
            "(id, name, config.category, config.description), return the top 3 relevant template Ids in a Json list"
        """

    def tools(self):
        return [fetch_template_tool]

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        #TODO: we need to check as well if we've a template already present for the customer
        # Fetch template from tool (We'll change it to LLM if we have multiple tool so we can decide which one to use)
        templates: List[Dict[str, Any]] = fetch_template_tool.invoke({})

        user_query = state.get("user_message", "")
        prompt = f""""
            {self.system_prompt()}
            User request: {user_query}
            Templates (JSON): {templates}
            
            Return strictly JSON array of 1-3 template IDs
        """
        try:
            ids_text = None #llm_complete(prompt)  # .md format or \n
            ids = (ids_text.replace("\n", "")
                   .replace("[", "")
                   .replace("]", "")
                   .replace("```", "")
                   .replace("json", "")
                   .replace("\"", "")
                   .split()) # [123, 345, 789]
            print("ID's", ids)
            candidate_templates = [t for t in templates if t["id"] in ids]
            state["candidate_templates"] = candidate_templates
        except Exception as e:
            state["candidate_templates"] = templates

        state["reply"] = "Please choose a template by id."
        state["status"] = "need_template_choice"
        return state