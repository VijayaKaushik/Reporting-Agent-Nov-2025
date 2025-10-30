"""
Create Template Agent

Responsible for:

Guiding users to create a new report template when no existing template matches their needs
Suggesting available columns and filters from the master schema
Collecting template metadata: name, description, selected columns, and optional filters
Validating and confirming user inputs interactively
Registering the new template via a REST API (create_template_tool)
Updating the workflow state to transition smoothly to the User Input Collector Agent
"""

from typing import Dict, Any, List

from langchain_core.tools import BaseTool

from app.agents.base_agent import BaseAgent
##from app.tools.fetch_template import describe_template_tool,fetch_template_tool add teal tools

class CreateTemplateAgent(BaseAgent):
    """
    Agent responsible for guiding users to create a new report template.

    This agent helps users define a custom template by:
    - Suggesting columns from the master schema
    - Asking for template name and description
    - Validating and confirming additional fields
    - Registering the template via an API
    """

    def name(self) -> str:
        return "create_template_agent"

    def system_prompt(self) -> str:
        return """
You are a **Template Creation Agent** for a report generation system.

Your job is to help users create a new report template when no existing template matches their needs.
You must use the tools provided to fetch column metadata and create the template.

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════════════════════

- **create_template_tool** → Register a new template using provided configuration
- **fetch_master_columns_tool** → Fetch available columns and filters for a template

═══════════════════════════════════════════════════════════════════════════════
YOUR RESPONSIBILITIES
═══════════════════════════════════════════════════════════════════════════════

1. **Understand User Intent**
   - Identify what kind of report user wants
   - Ask clarifying questions if intent is unclear

2. **Guide Template Creation**
   - Suggest columns and filters from master schema
   - Ask for template name, description, and additional columns
   - Validate user inputs interactively

3. **Register Template**
   - Use create_template_tool with collected information
   - Confirm creation and return template ID to state

4. **Transition to Next Step**
   - Set state["selected_template_id"] to the newly created template
   - Set state["template_config"] with returned config
   - Extract required fields into state["missing_fields"]
   - Set workflow_stage to "input_collection" and template_next_step to "user_input_collector"

═══════════════════════════════════════════════════════════════════════════════
CONVERSATION PATTERNS
═══════════════════════════════════════════════════════════════════════════════

**Pattern 1: Start Creation**
User: "I don’t see a template I need"
You: "No problem! Let's create a new report template. What should we name it?"

**Pattern 2: Column Selection**
You: "Here are the available columns you can include:
      • Participant Status
      • Tax Region
      • Officer Code
Which columns do you want in your report?"

**Pattern 3: Confirm & Create**
User: "Include all the suggested columns"
You: [Call create_template_tool]
     "Template 'Participant Demographics Custom' has been created successfully! Let's proceed to provide the required report details."
"""

    def tools(self) -> List[BaseTool]:
        """Return all tools available to this agent"""
        return [
            fetch_master_columns_tool,
            create_template_tool
        ]

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the template creation flow:
        - Collects template name, description, columns
        - Validates user selections
        - Calls create_template_tool
        - Updates state for next agent
        """
        # Extract state
        user_message = state.get("user_message", "")
        collected_data = state.get("create_template_data", {})

        # Step 1: Ask for template name if not provided
        if "name" not in collected_data:
            state["reply"] = "What would you like to name this new report template?"
            return state

        # Step 2: Ask for description if not provided
        if "description" not in collected_data:
            collected_data["name"] = user_message  # user provided template name
            state["create_template_data"] = collected_data
            state["reply"] = f"Great! Please provide a short description for **{collected_data['name']}**."
            return state

        # Step 3: Ask for columns if not provided
        if "columns" not in collected_data:
            collected_data["description"] = user_message  # user provided description
            # Fetch master columns
            master_columns = fetch_master_columns_tool()
            state["create_template_data"] = collected_data
            state["reply"] = (
                f"Here are the available columns you can include:\n" +
                "\n".join(f"• {c}" for c in master_columns) +
                "\nWhich columns would you like to include?"
            )
            return state

        # Step 4: Collect selected columns
        if "columns" not in collected_data or not collected_data["columns"]:
            collected_data["columns"] = [c.strip() for c in user_message.split(",")]
            state["create_template_data"] = collected_data

        # Step 5: Call create_template_tool
        template_config = create_template_tool(
            name=collected_data["name"],
            description=collected_data["description"],
            columns=collected_data["columns"]
        )

        # Step 6: Update state and transition
        state["selected_template_id"] = template_config["id"]
        state["template_config"] = template_config
        state["missing_fields"] = template_config.get("config", {}).get("required_fields", [])
        state["template_next_step"] = "user_input_collector"
        state["workflow_stage"] = "input_collection"
        state["reply"] = (
            f"Template '{collected_data['name']}' created successfully! "
            "Let's proceed to provide the required report details."
        )

        # Clear temporary create_template_data
        state.pop("create_template_data", None)

        return state
