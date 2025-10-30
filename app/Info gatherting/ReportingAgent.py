"""
Reporting Agent

Responsible for:
Scheduling reports based on the selected template and user-provided parameters
Validating that all required fields are collected before scheduling
Calling the scheduling API (schedule_report_tool) to create report execution
Providing confirmation to the user, including next run time and output URL
Checking report status or history via get_report_status_tool
Updating the workflow state with scheduled report ID, status, and output details
Handling user queries about existing reports, rescheduling, or delivery options
"""

from typing import Dict, Any, List

from langchain_core.tools import BaseTool

from app.agents.base_agent import BaseAgent
##from app.tools.fetch_template import describe_template_tool,fetch_template_tool add teal tools



class ReportingAgent(BaseAgent):
    """
    Agent responsible for scheduling and managing report executions.

    This agent helps users:
    - Schedule reports based on selected template and collected fields
    - Show report status and last/next run details
    - Provide output URLs once reports are generated
    """

    def name(self) -> str:
        return "reporting_agent"

    def system_prompt(self) -> str:
        return """
You are a **Reporting Agent** for a report generation system.

Your role is to help users schedule reports and manage their execution. 
You must always use the provided tools to perform actions or fetch status information.

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════════════════════

- **schedule_report_tool** → Schedule a report based on template ID and user-provided parameters
- **get_report_status_tool** → Fetch status of an existing scheduled report, including last run, next run, and output URL

═══════════════════════════════════════════════════════════════════════════════
YOUR RESPONSIBILITIES
═══════════════════════════════════════════════════════════════════════════════

1. **Schedule Reports**
   - Collect all required fields from state
   - Call schedule_report_tool with parameters like report name, frequency, run date, filters
   - Confirm scheduling to user with output URL or scheduled time

2. **Show Report Status**
   - Respond to queries like "When will my report be ready?" or "Show me my reports"
   - Use get_report_status_tool to fetch latest status
   - Provide friendly, clear status messages

3. **Transition Workflow**
   - Update state with scheduled report ID, status, and output URL
   - Clear temporary fields used for scheduling
   - Maintain workflow_stage = "reporting" or "completed"

═══════════════════════════════════════════════════════════════════════════════
CONVERSATION PATTERNS
═══════════════════════════════════════════════════════════════════════════════

**Pattern 1: Schedule a Report**
User: "Run the demographic report every Monday at 9 AM"
You: [Call schedule_report_tool]
     "Your report 'Participant Demographics' has been scheduled! 
      It will run every Monday at 9 AM. You can access it here: [URL]"

**Pattern 2: Check Report Status**
User: "What's the status of my report?"
You: [Call get_report_status_tool]
     "Your report 'Participant Demographics' last ran on 2025-10-28 09:00 AM. 
      Next run: 2025-11-04 09:00 AM. Output URL: [URL]"

**Pattern 3: Update Scheduling Parameters**
User: "Change the schedule to daily"
You: [Call schedule_report_tool with updated frequency]
     "Schedule updated! Your report will now run daily at 9 AM."

═══════════════════════════════════════════════════════════════════════════════
STATE MANAGEMENT
═══════════════════════════════════════════════════════════════════════════════

- `selected_template_id` → ID of template being reported
- `template_config` → Full template configuration
- `missing_fields` → Should be empty when reporting_agent is called
- `scheduled_report_id` → ID returned by schedule_report_tool
- `report_status` → Current status from get_report_status_tool
- `workflow_stage` → "reporting" or "completed"

═══════════════════════════════════════════════════════════════════════════════
IMPORTANT RULES
═══════════════════════════════════════════════════════════════════════════════

1. Never schedule without a template and all required fields
2. Always confirm scheduling and provide output URL
3. Handle queries about existing scheduled reports using get_report_status_tool
4. Maintain a clear, user-friendly response format
"""

    def tools(self) -> List[BaseTool]:
        """Return all tools available to this agent"""
        return [
            schedule_report_tool,
            get_report_status_tool
        ]

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute reporting actions based on user input and workflow state.
        """
        user_message = state.get("user_message", "")
        template_id = state.get("selected_template_id")
        template_config = state.get("template_config", {})
        missing_fields = state.get("missing_fields", [])

        # Validate that all required fields are collected
        if missing_fields:
            state["reply"] = (
                "Some required fields are missing. Please provide all necessary details "
                "before scheduling the report."
            )
            return state

        # Determine if user wants status or scheduling
        if "status" in user_message.lower() or "show" in user_message.lower():
            # Fetch report status
            report_id = state.get("scheduled_report_id")
            if not report_id:
                state["reply"] = "No report has been scheduled yet."
                return state
            status_info = get_report_status_tool(report_id)
            state["report_status"] = status_info
            state["reply"] = (
                f"Report '{status_info['name']}' last ran on {status_info['last_run']}. "
                f"Next run: {status_info['next_run']}. Output URL: {status_info['output_url']}"
            )
            return state

        # Otherwise, schedule the report
        schedule_params = {
            "template_id": template_id,
            "report_name": template_config.get("name", "New Report"),
            "frequency": state.get("frequency", "once"),
            "run_date": state.get("run_date"),
            "start_date": state.get("start_date"),
            "end_date": state.get("end_date"),
            "delivery_method": state.get("delivery_method", "email"),
            "delivery_target": state.get("delivery_target"),
            "config_override": state.get("user_inputs", {}),
        }

        # Call scheduling tool
        scheduled_report = schedule_report_tool(**schedule_params)

        # Update state
        state["scheduled_report_id"] = scheduled_report["id"]
        state["report_status"] = scheduled_report["status"]
        state["workflow_stage"] = "reporting"
        state["reply"] = (
            f"Report '{schedule_params['report_name']}' has been scheduled successfully! "
            f"Next run: {scheduled_report['next_run']}. Output URL: {scheduled_report['output_url']}"
        )

        return state
