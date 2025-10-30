"""
Existing Template Agent

Discovering available report templates based on user intent or keywords
Searching and filtering templates by category, name, or description
Presenting template options to the user in a clear, user-friendly way
Retrieving detailed template configuration for a selected template
Guiding users through template comparison and exploration
Updating the workflow state with the selected template and required fields for reporting
"""

from typing import Dict, Any, List

from langchain_core.tools import BaseTool

from app.agents.base_agent import BaseAgent
##from app.tools.fetch_template import describe_template_tool,fetch_template_tool add teal tools



class ExistingTemplateAgent(BaseAgent):
    """
    Agent responsible for template discovery, search, and selection.
    
    This agent helps users find the right report template by:
    - Searching through available templates
    - Filtering by categories or keywords
    - Providing detailed template descriptions
    - Guiding template selection
    """
    
    def name(self) -> str:
        return "template_agent"
    
    def system_prompt(self) -> str:
        return """
[Include your full system prompt here, as defined above]
"""
    
    def tools(self) -> List[BaseTool]:
        """Return all tools available to this agent"""
        return [
            fetch_template_tool,
            describe_template_tool
        ]
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes template discovery or selection based on user input.
        Updates state with search results, selected template, and next step.
        """
        user_message = state.get("user_message", "")
        selected_template = state.get("selected_template_id")
        workflow_stage = state.get("workflow_stage", "discovery")
        template_search_results = state.get("template_search_results", [])

        # Step 1: If template is already selected, show details
        if selected_template:
            template_config = describe_template_tool(template_id=selected_template)
            state["template_config"] = template_config
            state["missing_fields"] = template_config.get("config", {}).get("required_fields", [])
            state["template_next_step"] = "user_input_collector"
            state["workflow_stage"] = "input_collection"
            state["reply"] = (
                f"✓ You've selected **{template_config['name']}**.\n"
                f"Required fields to continue: {state['missing_fields']}\n"
                f"Let's proceed to provide these values."
            )
            return state

        # Step 2: If no search results yet, search based on user message
        if not template_search_results:
            # Use LLM to rank or filter templates based on user message
            search_results = fetch_template_tool(search_query=user_message)
            state["template_search_results"] = search_results

            if not search_results:
                # No matching templates: offer categories
                search_results = fetch_template_tool(search_query=None)
                state["template_search_results"] = search_results
                state["reply"] = (
                    "I couldn't find an exact match. Here are some template categories you can choose from:\n" +
                    "\n".join(f"• {t['category']}" for t in search_results[:5])
                )
            else:
                # Show top 3-5 results
                top_results = search_results[:5]
                state["reply"] = "I found these templates:\n" + "\n".join(
                    f"{i+1}. **{t['name']}** - {t['description']}" for i, t in enumerate(top_results)
                )
            return state

        # Step 3: Handle template selection from previous search results
        # Simple heuristic: match user input to template name
        matched_template = None
        for t in template_search_results:
            if user_message.lower() in t["name"].lower():
                matched_template = t
                break

        if matched_template:
            state["selected_template_id"] = matched_template["id"]
            template_config = describe_template_tool(template_id=matched_template["id"])
            state["template_config"] = template_config
            state["missing_fields"] = template_config.get("config", {}).get("required_fields", [])
            state["template_next_step"] = "user_input_collector"
            state["workflow_stage"] = "input_collection"
            state["reply"] = (
                f"Great! You've selected **{matched_template['name']}**.\n"
                f"Required fields: {state['missing_fields']}\n"
                "Let's provide these values to continue."
            )
        else:
            # Ask user to clarify selection
            state["reply"] = (
                "I couldn't identify which template you want. "
                "Please type the exact name or number from the list above."
            )

        return state
