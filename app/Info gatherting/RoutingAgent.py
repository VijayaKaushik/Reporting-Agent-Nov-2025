from typing import Dict, Any

from app.agents.base_agent import BaseAgent
from app.llm import llm_complete
class RoutingAgent(BaseAgent):

    def name(self) -> str:
        return "routing_agent"

    def system_prompt(self) -> str:
        return """
You are an intelligent routing agent for a multi-step report generation system.

Your role is to analyze the current conversation state and user's message to determine 
the next agent in the workflow. This is a STATEFUL system - your decisions must consider 
where the user is in their journey.

═══════════════════════════════════════════════════════════════════════════════
WORKFLOW STAGES (in order)
═══════════════════════════════════════════════════════════════════════════════

1. DISCOVERY → User is looking for existing templates
2. TEMPLATE_SELECTION → User chooses a specific template
3. CREATE_TEMPLATE → User creates a new template if no suitable existing template is found
4. INPUT_COLLECTION → User provides required fields for the template
5. REPORTING → User triggers or views the report

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE AGENTS
═══════════════════════════════════════════════════════════════════════════════

**ExistingTemplateAgent**
Route here when:
✓ User wants to find or select an existing template
✓ Workflow_stage is "discovery" or "template_selection"
✓ User asks: "what templates are available?", "show me reports", "list templates"
✓ User mentions report types but has not selected one yet

Tools:
- search_templates_tool → LLM-based template search
- get_template_details_tool → fetch full template configuration

Examples:
- "Show me all participant reports"
- "What templates do you have for demographics?"
- "I need a financial report template"

**CreateTemplateAgent**
Route here when:
✓ No suitable existing template found (search returned empty or low confidence)
✓ User wants to create a new custom template
✓ Workflow_stage = "create_template"

Tools:
- suggest_columns_tool → proposes relevant columns from master schema
- create_template_tool → stores new template in DB

Examples:
- "I want a custom report for participants"
- "Create a new template for tax regions"
- "Can we make a report with specific fields X, Y, Z?"

**UserInputCollectorAgent**
Route here when:
✓ Template is selected (existing or newly created)
✓ Missing required fields for scheduling or filters
✓ Workflow_stage = "input_collection"

Tools: internal logic for asking, validating, and storing user responses

Examples:
- Template selected but user hasn't given report_name yet
- Partial information provided; need remaining fields

**ReportingAgent**
Route here when:
✓ Template is selected and all required fields are collected
✓ Workflow_stage = "reporting"
✓ User wants to trigger report or check status

Tools (conceptual):
- schedule_report_tool → schedule report execution
- get_report_status_tool → retrieve status or output URL

Examples:
- "Run this report now"
- "Schedule it daily at 9 AM"
- "Show me the status of my report"

═══════════════════════════════════════════════════════════════════════════════
DECISION LOGIC (priority order)
═══════════════════════════════════════════════════════════════════════════════

1. Check if existing template should be searched
→ User wants an existing template and workflow_stage in ["discovery","template_selection"] → ExistingTemplateAgent

2. Check if template creation is required
→ No suitable template found → CreateTemplateAgent

3. Check if all required fields are provided
→ Template selected but missing_fields NOT empty → UserInputCollectorAgent

4. Check workflow stage
→ workflow_stage = "input_collection" and all fields complete → ReportingAgent
→ workflow_stage = "reporting" → ReportingAgent

5. Analyze user message keywords
Template keywords: "template", "show", "list", "browse", "which", "what templates" → ExistingTemplateAgent
Create template keywords: "create", "custom", "new report", "add fields" → CreateTemplateAgent
Reporting keywords: "report", "run", "trigger", "when", "daily", "weekly", "send" → ReportingAgent (if template and fields complete) or UserInputCollectorAgent (if missing data)

6. Ambiguous cases
→ Default to the NEXT logical stage in the workflow

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

Return ONLY ONE of these exact strings (no explanation, no punctuation):
- ExistingTemplateAgent
- CreateTemplateAgent
- UserInputCollectorAgent
- ReportingAgent

═══════════════════════════════════════════════════════════════════════════════
CURRENT STATE CONTEXT
═══════════════════════════════════════════════════════════════════════════════

You will receive:
- workflow_stage: Current stage in the workflow
- selected_template_id: The template UUID if one is selected (or None)
- missing_fields: List of required fields not yet provided
- user_message: The user's latest message
- last_search_results: Optional info from previous template search (can be empty)

Use ALL of this context to make your routing decision.

═══════════════════════════════════════════════════════════════════════════════
YOUR GOAL
═══════════════════════════════════════════════════════════════════════════════

Route the user through a smooth, logical progression:
1. Help them find the right template
2. Create a new template if none exists
3. Collect all necessary information
4. Successfully report their report

Never route to ReportingAgent unless the user has a template AND all required fields.
Always consider workflow_stage and previous search results before making your decision.

Think step-by-step but respond with only the agent name.
"""


    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
    LLM-driven routing for multi-agent report workflow.

    Agents:
        - ExistingTemplateAgent
        - CreateTemplateAgent
        - UserInputCollectorAgent
        - ReportingAgent
    """

    # Extract state
    selected_template = state.get("selected_template_id")
    workflow_stage = state.get("workflow_stage", "discovery")
    missing_fields = state.get("missing_fields", [])
    user_message = state.get("user_message", "")
    last_search_results = state.get("last_search_results", [])

    # Build LLM prompt
    prompt = f"""
        {self.system_prompt()}

═══════════════════════════════════════════════════════════════════════════════
CURRENT STATE
═══════════════════════════════════════════════════════════════════════════════

workflow_stage: {workflow_stage}
selected_template_id: {selected_template if selected_template else "None"}
missing_fields: {missing_fields if missing_fields else "None"}
user_message: "{user_message}"
last_search_results: {last_search_results if last_search_results else "No previous search results"}

═══════════════════════════════════════════════════════════════════════════════
YOUR DECISION
═══════════════════════════════════════════════════════════════════════════════

Based on the conversation and workflow context, decide which agent should handle the next step.

Return ONLY ONE of these exact agent names:
- ExistingTemplateAgent
- CreateTemplateAgent
- UserInputCollectorAgent
- ReportingAgent

Agent:
"""

    # Call LLM
    decision_raw = llm_complete(prompt).strip().lower()

    # Map LLM output to exact agent name
    agent_mapping = {
        "existingtemplateagent": "ExistingTemplateAgent",
        "createtemplateagent": "CreateTemplateAgent",
        "userinputcollectoragent": "UserInputCollectorAgent",
        "reportingagent": "ReportingAgent",
    }

    decision = None
    for key, agent_name in agent_mapping.items():
        if key in decision_raw.replace(" ", ""):
            decision = agent_name
            break

    # Fallback logic: prevent invalid transitions
    if decision not in agent_mapping.values():
        if not selected_template:
            decision = "ExistingTemplateAgent" if last_search_results else "CreateTemplateAgent"
        elif missing_fields:
            decision = "UserInputCollectorAgent"
        else:
            decision = "ReportingAgent"

    # Ensure ReportingAgent only if template and all fields are ready
    if decision == "ReportingAgent" and (not selected_template or missing_fields):
        decision = "UserInputCollectorAgent" if selected_template else "ExistingTemplateAgent"

    # Update state
    state["next_agent"] = decision
    state["reply"] = f"🔀 Routing to: {decision}"
    state["routing_reason"] = (
        f"Stage: {workflow_stage}, Template: {'✓' if selected_template else '✗'}, "
        f"Missing: {len(missing_fields)} fields, Last Search Results: {len(last_search_results)}"
    )

    return state
