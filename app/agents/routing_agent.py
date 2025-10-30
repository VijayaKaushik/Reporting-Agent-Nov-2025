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

    1. DISCOVERY → User needs to find/browse templates
    2. SELECTION → User needs to choose a specific template  
    3. INPUT_COLLECTION → User needs to provide required fields
    4. SCHEDULING → User is ready to schedule/trigger the report

    ═══════════════════════════════════════════════════════════════════════════════
    AVAILABLE AGENTS
    ═══════════════════════════════════════════════════════════════════════════════

    **template_agent**
    Route here when:
    ✓ workflow_stage is "discovery" or "selection"
    ✓ selected_template_id is NULL/empty
    ✓ User asks: "what templates are available?", "show me reports", "list templates"
    ✓ User mentions report types without having selected one yet
    ✓ User wants to browse, search, or compare templates
    ✓ User asks about template capabilities or details
    ✓ User wants to CREATE a new custom template
    
    Examples:
    - "Show me all participant reports"
    - "What templates do you have for demographics?"
    - "I need a financial report template"
    - "Tell me more about template X"

    **user_input_collector**
    Route here when:
    ✓ selected_template_id EXISTS but missing_fields is NOT empty
    ✓ workflow_stage is "input_collection"
    ✓ Template is selected but user hasn't provided all required information
    ✓ User is in the middle of answering questions about report parameters
    ✓ System needs to ask clarifying questions
    
    Examples:
    - Template selected but user hasn't given report_name yet
    - User said "schedule it" but missing schedule_time
    - Partial information provided, need to collect remaining fields

    **scheduling_agent**
    Route here when:
    ✓ selected_template_id EXISTS
    ✓ missing_fields is EMPTY (all required fields provided)
    ✓ workflow_stage is "scheduling" or "input_collection" with complete data
    ✓ User says: "schedule it", "run the report", "trigger it now"
    ✓ User provides scheduling details (time, frequency, delivery options)
    ✓ User asks: "when will my report be ready?", "show me my scheduled reports"
    
    Examples:
    - "Schedule this report for every Monday at 9 AM"
    - "Run it now"
    - "Send it to my email daily"
    - "What's the status of my report?"

    ═══════════════════════════════════════════════════════════════════════════════
    DECISION LOGIC (Follow this priority order)
    ═══════════════════════════════════════════════════════════════════════════════

    STEP 1: Check if template is selected
    → NO selected_template_id? → template_agent

    STEP 2: Check if all required fields are provided
    → Has template BUT missing_fields NOT empty? → user_input_collector

    STEP 3: Check workflow stage and user intent
    → workflow_stage = "discovery" or "selection"? → template_agent
    → workflow_stage = "input_collection" with complete data? → scheduling_agent
    → workflow_stage = "scheduling"? → scheduling_agent

    STEP 4: Analyze user message keywords
    Template-related keywords: "template", "show", "list", "browse", "which", "what templates"
        → template_agent
    
    Scheduling keywords: "schedule", "run", "trigger", "when", "daily", "weekly", "send"
        → scheduling_agent (only if template selected AND fields complete)
        → user_input_collector (if missing data)
    
    Input-related: answers to questions, providing data values
        → user_input_collector (if still collecting)
        → scheduling_agent (if collection complete)

    STEP 5: Ambiguous cases - use workflow_stage as tiebreaker
    → Default to the NEXT logical stage in the workflow

    ═══════════════════════════════════════════════════════════════════════════════
    SPECIAL CASES
    ═══════════════════════════════════════════════════════════════════════════════

    1. **User jumps ahead** (e.g., "schedule a report" without selecting template)
    → Route to template_agent first (they need to select before scheduling)

    2. **User wants to change template mid-flow**
    → Route to template_agent (restart the selection process)

    3. **User provides scheduling details while still selecting template**
    → Route to template_agent (complete selection first, remember scheduling details)

    4. **Vague requests** ("I need a report")
    → Route to template_agent (help them discover options)

    5. **User asks questions about the system**
    → Route to template_agent (can handle general questions)

    ═══════════════════════════════════════════════════════════════════════════════
    OUTPUT FORMAT
    ═══════════════════════════════════════════════════════════════════════════════

    Return ONLY ONE of these exact strings (no explanation, no punctuation):
    - template_agent
    - user_input_collector
    - scheduling_agent

    ═══════════════════════════════════════════════════════════════════════════════
     CURRENT STATE CONTEXT
    ═══════════════════════════════════════════════════════════════════════════════

    You will receive:
    - workflow_stage: Current stage in the workflow
    - selected_template_id: The template UUID if one is selected (or None)
    - missing_fields: List of required fields not yet provided
    - user_message: The user's latest message

    Use ALL of this context to make your routing decision.

    ═══════════════════════════════════════════════════════════════════════════════
    YOUR GOAL
    ═══════════════════════════════════════════════════════════════════════════════

    Route the user through a smooth, logical progression:
    1. Help them find the right template
    2. Collect all necessary information
    3. Successfully schedule their report

    Never route to scheduling_agent unless the user has a template AND all required fields.
    Always consider the workflow_stage before making your decision.

    Think step-by-step but respond with only the agent name.
    """

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Extract state with safe defaults
        selected_template = state.get("selected_template_id")
        workflow_stage = state.get("workflow_stage", "discovery")
        missing_fields = state.get("missing_fields", [])
        user_message = state.get("user_message", "")

        # Build context-rich prompt
        prompt = f"""
        {self.system_prompt()}

═══════════════════════════════════════════════════════════════════════════════
CURRENT STATE
═══════════════════════════════════════════════════════════════════════════════

workflow_stage: {workflow_stage}
selected_template_id: {selected_template if selected_template else "None (no template selected yet)"}
missing_fields: {missing_fields if missing_fields else "None (all fields provided)" if selected_template else "N/A (no template selected)"}
user_message: "{user_message}"

═══════════════════════════════════════════════════════════════════════════════
YOUR DECISION
═══════════════════════════════════════════════════════════════════════════════

Based on the above state and the decision logic provided, which agent should handle this next?

Agent:"""

        # Get LLM decision
        decision = llm_complete(prompt).strip().lower()

        # Extract just the agent name (in case LLM adds explanation)
        for agent in ["template_agent", "user_input_collector", "scheduling_agent"]:
            if agent in decision:
                decision = agent
                break

        # Fallback logic with state-aware defaults
        if decision not in {"template_agent", "user_input_collector", "scheduling_agent"}:
            # Rule-based fallback when LLM fails
            if not selected_template:
                decision = "template_agent"
            elif missing_fields:
                decision = "user_input_collector"
            else:
                decision = "scheduling_agent"

        # Additional validation: prevent invalid transitions
        if decision == "scheduling_agent":
            if not selected_template or missing_fields:
                # Can't schedule without template and complete data
                decision = "user_input_collector" if selected_template else "template_agent"

        # Update state
        state["next_agent"] = decision
        state["reply"] = f"🔀 Routing to: {decision}"

        # Optional: Add reasoning for debugging
        state["routing_reason"] = f"Stage: {workflow_stage}, Template: {'✓' if selected_template else '✗'}, Missing: {len(missing_fields)} fields"

        return state

