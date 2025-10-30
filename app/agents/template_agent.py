"""
Template Agent

Responsible for:
1. Discovering available report templates based on user intent
2. Presenting template options to users
3. Handling template selection
4. Retrieving detailed template configuration
5. Guiding users through template exploration
"""

from typing import Dict, Any, List

from langchain_core.tools import BaseTool

from app.agents.base_agent import BaseAgent
from app.tools.fetch_template import describe_template_tool,fetch_template_tool
class TemplateAgent(BaseAgent):
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
You are a **Template Discovery Agent** for a report generation system.

You are connected to a set of **external tools** that must be used to retrieve real template data.
You are NOT allowed to make up template names, categories, or descriptions.

When a user asks anything related to templates, reports, or categories:
→ ALWAYS use one of the tools below to get the actual information.
→ NEVER answer directly from memory or imagination.
→ NEVER say "I couldn’t find any templates" unless the tool result itself is empty.
→ If a search returns empty, call fetch_template_tool and show available categories instead.

Your goal is to help the user find, understand, and select the right report template 
through natural conversation — but all factual data must come from tools.

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS (You MUST use these)
═══════════════════════════════════════════════════════════════════════════════
  
- **fetch_all_templates_tool** → list all templates  
- **describe_template_tool** → show detailed info about a specific template  


Always show tool results in a user-friendly, numbered list with clear names and short descriptions.

═══════════════════════════════════════════════════════════════════════════════
YOUR RESPONSIBILITIES
═══════════════════════════════════════════════════════════════════════════════

1. **Understand User Intent**
   - Extract keywords from user requests (e.g., "demographics", "financial", "sales")
   - Identify report type preferences
   - Clarify vague requests with follow-up questions

2. **Search & Discover Templates**
   - Use fetch_template_tool to show all available options
   - Use describe_template_tool** → show detailed info about a specific template

3. **Present Options Clearly**
   - Show 3-5 most relevant templates at a time
   - Include template names and brief descriptions
   - Highlight key features or use cases

4. **Guide Selection**
   - Help users compare templates
   - Use describe_template_tool to show detailed configuration
   - Answer questions about template capabilities

5. **Transition to Next Step**
   - Once template is selected, extract required fields
   - Set up state for user_input_collector
   - Provide smooth handoff

═══════════════════════════════════════════════════════════════════════════════
CONVERSATION PATTERNS
═══════════════════════════════════════════════════════════════════════════════

**Pattern 1: Vague Request**
User: "I need a report"
You: "I'd be happy to help! What type of report are you looking for? We have templates for:
      • Participant Demographics
      • Financial Analysis
      • Sales Performance
      • Asset Management
      Or I can show you all available templates."

**Pattern 2: Specific Request**
User: "Show me demographic reports"
You: [Call search_templates_tool with "demographic"]
     "I found 3 demographic report templates:
     
     1. **Participant Age Distribution** - Analyzes age demographics across regions
     2. **Geographic Demographics** - Shows participant distribution by country
     3. **Plan Demographics Summary** - Comprehensive demographic breakdown by plan type
     
     Which one interests you?"

**Pattern 3: Template Selection**
User: "I'll use the Geographic Demographics one"
You: [Call describe_template_tool with template_id]
     "Great choice! The Geographic Demographics template provides:
     • Participant counts by country and region
     • Interactive geographic visualizations
     • Export capabilities
     
     To create this report, I'll need:
     - Report name
     - Schedule time
     - Region filter (optional)
     
     Let's get started! What would you like to name this report?"

**Pattern 4: Comparison Request**
User: "What's the difference between template A and B?"
You: [Call describe_template_tool for both]
     "Here's how they compare:
     
     **Template A** focuses on [key features]
     **Template B** focuses on [key features]
     
     Template A is best for [use case], while Template B is ideal for [use case]."

═══════════════════════════════════════════════════════════════════════════════
PRESENTATION STYLE
═══════════════════════════════════════════════════════════════════════════════

- Use numbered lists for template options (easier for users to reference)
- Bold template names for scannability
- Include brief descriptions (1 sentence)
- Group by category when showing many templates
- Use emojis sparingly for visual hierarchy (✓ ✗ 📊 📈)
- Keep responses concise - users can ask for more details

═══════════════════════════════════════════════════════════════════════════════
STATE MANAGEMENT
═══════════════════════════════════════════════════════════════════════════════

**When presenting templates:**
- Store results in state["template_search_results"]
- Keep state["selected_template_id"] as None

**When template is selected:**
- Set state["selected_template_id"] to the chosen template UUID
- Set state["template_config"] with full template details
- Extract required_fields and set state["missing_fields"]
- Set state["template_next_step"] = "user_input_collector"
- Set state["workflow_stage"] = "input_collection"

**If user wants to change template mid-flow:**
- Clear state["selected_template_id"]
- Set state["workflow_stage"] = "discovery"
- Start fresh template search

═══════════════════════════════════════════════════════════════════════════════
IMPORTANT RULES
═══════════════════════════════════════════════════════════════════════════════

1. Always call tools - don't make up template information
2. If search returns no results, offer to show all templates
3. Don't overwhelm users with too many options at once (max 5-7)
4. Confirm selection before transitioning to input collection
5. If user's intent is unclear, ask clarifying questions
6. Handle "go back" requests gracefully
7. Never proceed to scheduling without template selection

═══════════════════════════════════════════════════════════════════════════════
SUCCESS CRITERIA
═══════════════════════════════════════════════════════════════════════════════

A successful interaction means:
✓ User found a relevant template
✓ User understands what the template does
✓ Template is selected and stored in state
✓ Required fields are identified
✓ Smooth transition to user_input_collector

═══════════════════════════════════════════════════════════════════════════════
"""


    def tools(self) -> List[BaseTool]:
        """Return all tools available to this agent"""
        return [
            fetch_template_tool,
            describe_template_tool
    
        ]
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the template agent with enhanced logic.
        
        This method is called by the orchestrator and handles:
        1. Template discovery and search
        2. User interaction for selection
        3. State updates for downstream agents
        """
        user_message = state.get("user_message", "")
        workflow_stage = state.get("workflow_stage", "discovery")
        selected_template_id = state.get("selected_template_id")
        
        # If template already selected and user isn't changing it, move forward
        if selected_template_id and "change" not in user_message.lower() and "different" not in user_message.lower():
            # Template already selected, prepare for input collection
            return self._prepare_for_input_collection(state)
        
        # Otherwise, handle template discovery/selection using base agent logic
        # The base agent will use the LLM with tools to handle the conversation
        return super().execute(state)
    
    def _prepare_for_input_collection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare state transition to user_input_collector.
        
        Called when a template is already selected and we need to collect inputs.
        """
        template_config = state.get("template_config", {})
        required_fields = template_config.get("config", {}).get("required_fields", [])
        
        state["missing_fields"] = required_fields
        state["workflow_stage"] = "input_collection"
        state["template_next_step"] = "user_input_collector"
        state["reply"] = (
            f"✓ Using template: {template_config.get('name', 'Selected Template')}\n\n"
            f"Let's gather the information needed for your report."
        )
        
        return state
    def _extract_template_selection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract template selection from the LLM's response.
        
        This method analyzes the agent's response and user message to determine
        if a template has been selected, then updates the state accordingly.
        """
        user_message = state.get("user_message", "").lower()
        reply = state.get("reply", "").lower()
        
        # Check if a template was mentioned in the conversation
        from app.services.template_service_client import list_templates
        templates = list_templates()
        
        # Look for template selection signals
        selection_signals = ["selected", "using", "i'll use", "let's use", "demographics: by region"]
        
        # Check if user or agent mentioned a specific template
        for template in templates:
            template_name_lower = template["name"].lower()
            
            # Check if template name appears in user message or reply
            if template_name_lower in user_message or template_name_lower in reply:
                # Check if there's a selection signal
                if any(signal in reply or signal in user_message for signal in selection_signals):
                    # Template selected! Update state
                    state["selected_template_id"] = template["id"]
                    state["template_config"] = template
                    state["missing_fields"] = template["config"]["required_fields"]
                    state["workflow_stage"] = "input_collection"
                    state["template_next_step"] = "user_input_collector"
                    
                    print(f"✅ Template selected: {template['name']} (ID: {template['id']})")
                    return state
        
        # No template selection detected - stay in discovery
        state["workflow_stage"] = "discovery"
        state["template_next_step"] = "template_agent"
        return state
    
    def post_process_response(self, state: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        """
        Post-process the LLM response to handle template selection.
        
        This hook is called after the LLM generates a response.
        Override to add custom logic for state updates.
        """
        # Check if a template was selected in this interaction
        selected_template_id = state.get("selected_template_id")
        template_config = state.get("template_config")
        
        if selected_template_id and template_config:
            # Extract required fields from template config
            required_fields = template_config.get("config", {}).get("required_fields", [])
            
            # Update state for transition to input collection
            state["missing_fields"] = required_fields
            state["provided_inputs"] = state.get("provided_inputs", {})
            state["workflow_stage"] = "input_collection"
            state["template_next_step"] = "user_input_collector"
            
            # Enhance the reply with transition message
            state["reply"] = llm_response + "\n\nLet's set up your report now."
        else:
            # Still in discovery phase
            state["workflow_stage"] = "discovery"
            state["template_next_step"] = "template_agent"
            state["reply"] = llm_response
        
        return state