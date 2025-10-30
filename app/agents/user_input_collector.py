"""
User Input Collector Agent

This agent is responsible for:
1. Identifying what required fields are still missing
2. Asking the user for missing information in a conversational way
3. Validating and storing user responses
4. Determining when all required fields are collected
5. Transitioning to the scheduling agent when ready
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from app.agents.base_agent import BaseAgent
from app.llm import llm_complete


class UserInputCollectorAgent(BaseAgent):
    
    def name(self) -> str:
        return "user_input_collector"
    
    def system_prompt(self) -> str:
        return """
You are a User Input Collector Agent for a report scheduling system.

Your job is to collect missing required fields from the user in a friendly, 
conversational manner.

═══════════════════════════════════════════════════════════════════════════════
 YOUR RESPONSIBILITIES
═══════════════════════════════════════════════════════════════════════════════

1. **Identify Missing Fields**: Review the missing_fields list
2. **Ask Contextual Questions**: Request information naturally based on field type
3. **Extract Information**: Parse user's response to extract field values
4. **Validate Input**: Ensure data is in the correct format
5. **Update State**: Store collected values and update missing_fields list
6. **Determine Next Step**: Decide if more collection needed or ready for scheduling

═══════════════════════════════════════════════════════════════════════════════
COMMON FIELD TYPES & HOW TO COLLECT THEM
═══════════════════════════════════════════════════════════════════════════════

**report_name**
  - Ask: "What would you like to name this report?"
  - Examples: "Monthly Sales Report", "Q4 Demographics Summary"
  - Validation: Non-empty string

**schedule_time**
  - Ask: "When would you like to schedule this report?" or "How often should it run?"
  - Examples: "Every Monday at 9 AM", "Daily at 8:00", "First day of month"
  - Accept: Natural language time expressions
  - Extract: frequency (daily/weekly/monthly), time, day_of_week, day_of_month

**region**
  - Ask: "Which region(s) should this report cover?"
  - Examples: "North America", "EMEA", "All regions", "US, Canada"
  - Accept: Single or comma-separated list

**date_range**
  - Ask: "What date range should the report cover?"
  - Examples: "Last 30 days", "January 2024", "Q1 2024", "2024-01-01 to 2024-03-31"
  - Accept: Natural language or ISO format

**asset_types**
  - Ask: "Which asset types should be included?"
  - Examples: "All assets", "Stocks, Bonds", "Real Estate"
  - Accept: Comma-separated list or "all"

**delivery_method**
  - Ask: "How would you like to receive the report?"
  - Examples: "Email", "Dashboard", "Both"
  - Options: email, dashboard, slack, download

**email_recipients**
  - Ask: "Who should receive this report?" or "What email addresses?"
  - Examples: "john@company.com", "team@company.com, manager@company.com"
  - Validation: Valid email format(s)

═══════════════════════════════════════════════════════════════════════════════
CONVERSATION STYLE
═══════════════════════════════════════════════════════════════════════════════

- Be conversational and friendly, not robotic
- Ask for ONE field at a time (don't overwhelm the user)
- Acknowledge what they've already provided
- Use context from the template name to guide questions
- Provide examples when helpful
- Handle clarifications gracefully

Good: "Great! What would you like to name this report?"
Bad: "Enter report_name:"

Good: "Perfect. When would you like to schedule it? (e.g., 'Every Monday at 9 AM')"
Bad: "Provide schedule_time in ISO format"

═══════════════════════════════════════════════════════════════════════════════
EXTRACTING VALUES FROM USER RESPONSES
═══════════════════════════════════════════════════════════════════════════════

User responses can be:
1. **Direct answers**: "Monthly Sales Report"
2. **Conversational**: "I'd like to call it the Weekly Summary"
3. **Multi-field**: "Call it Q4 Report and schedule it for Mondays at 9 AM"

Your task:
- Extract the actual value(s) from conversational text
- Match extracted values to the appropriate field names
- Handle multiple values if user provides several fields at once

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

You must return a JSON object with this structure:
{
  "extracted_fields": {
    "field_name": "extracted_value",
    ...
  },
  "still_missing": ["field1", "field2", ...],
  "next_question": "What you'll ask next (or null if done)",
  "ready_for_scheduling": true/false
}

Example:
{
  "extracted_fields": {
    "report_name": "Monthly Demographics Report"
  },
  "still_missing": ["schedule_time"],
  "next_question": "Great! When would you like to schedule this report?",
  "ready_for_scheduling": false
}

═══════════════════════════════════════════════════════════════════════════════
IMPORTANT RULES
═══════════════════════════════════════════════════════════════════════════════

1. Only ask for fields that are in the missing_fields list
2. Don't re-ask for fields already in provided_inputs
3. If user provides multiple fields at once, extract all of them
4. Set ready_for_scheduling=true ONLY when still_missing is empty
5. Be robust to typos and variations in user responses
6. If you can't extract a value, ask for clarification
7. Always return valid JSON

═══════════════════════════════════════════════════════════════════════════════
"""

    def tools(self) -> List:
        """No tools needed - this agent uses LLM reasoning"""
        return []
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution logic for collecting user inputs
        """
        # Extract current state
        user_message = state.get("user_message", "")
        missing_fields = state.get("missing_fields", [])
        provided_inputs = state.get("provided_inputs", {})
        selected_template_id = state.get("selected_template_id")
        template_config = state.get("template_config", {})
        
        # If no missing fields, we're done
        if not missing_fields:
            state["workflow_stage"] = "scheduling"
            state["reply"] = "✅ All required information collected! Proceeding to schedule your report."
            state["template_next_step"] = "scheduling_agent"
            return state
        
        # Build context for LLM
        context = self._build_context(
            user_message=user_message,
            missing_fields=missing_fields,
            provided_inputs=provided_inputs,
            template_config=template_config
        )
        
        # Get LLM to extract fields and generate next question
        extraction_result = self._extract_fields(context)
        
        # Update state with extracted fields
        if extraction_result.get("extracted_fields"):
            provided_inputs.update(extraction_result["extracted_fields"])
            state["provided_inputs"] = provided_inputs
            
            # Update missing fields list
            for field in extraction_result["extracted_fields"].keys():
                if field in missing_fields:
                    missing_fields.remove(field)
        
        state["missing_fields"] = extraction_result.get("still_missing", missing_fields)
        
        # Determine next step
        if extraction_result.get("ready_for_scheduling", False):
            state["workflow_stage"] = "scheduling"
            state["template_next_step"] = "scheduling_agent"
            state["reply"] = extraction_result.get("next_question") or "✅ Perfect! I have all the information needed. Let me schedule your report."
        else:
            # Need to collect more - stay in input collection
            state["workflow_stage"] = "input_collection"
            state["template_next_step"] = "user_input_collector"
            state["reply"] = extraction_result.get("next_question") or self._generate_next_question(missing_fields)
        
        return state
    
    def _build_context(
        self,
        user_message: str,
        missing_fields: List[str],
        provided_inputs: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> str:
        """Build context string for the LLM"""
        
        template_name = template_config.get("name", "Unknown Template")
        
        context = f"""
═══════════════════════════════════════════════════════════════════════════════
CURRENT CONTEXT
═══════════════════════════════════════════════════════════════════════════════

**Selected Template**: {template_name}

**Already Provided**:
{self._format_dict(provided_inputs) if provided_inputs else "  None yet"}

**Still Missing**:
{', '.join(missing_fields) if missing_fields else "None - all fields collected!"}

**User's Latest Message**:
"{user_message}"

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════════════════════

1. Extract any field values from the user's message
2. Determine which fields are still missing
3. Generate the next question to ask (or confirm completion)
4. Return the result as JSON

Remember: Extract values from conversational text, not just direct answers.
"""
        return context
    
    def _extract_fields(self, context: str) -> Dict[str, Any]:
        """Use LLM to extract fields from user message"""
        
        prompt = f"""
{self.system_prompt()}

{context}

Now, analyze the user's message and return a JSON response following the output format specified above.
Return ONLY valid JSON, no other text.

JSON Response:
"""
        
        try:
            response = llm_complete(prompt)
            
            # Extract JSON from response (handle cases where LLM adds extra text)
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            import json
            result = json.loads(response)
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            return result
            
        except Exception as e:
            # Fallback if LLM fails to return valid JSON
            print(f"⚠️ Failed to parse LLM response: {e}")
            return self._fallback_extraction(context)
    
    def _fallback_extraction(self, context: str) -> Dict[str, Any]:
        """Simple rule-based extraction as fallback"""
        # This is a safety net - extract from context manually
        # In practice, you'd implement pattern matching here
        
        return {
            "extracted_fields": {},
            "still_missing": [],  # Will be set by caller
            "next_question": "I'd be happy to help with that. Could you provide a bit more detail?",
            "ready_for_scheduling": False
        }
    
    def _generate_next_question(self, missing_fields: List[str]) -> str:
        """Generate a question for the next missing field"""
        
        if not missing_fields:
            return "✅ All information collected!"
        
        next_field = missing_fields[0]
        
        # Map field names to user-friendly questions
        questions = {
            "report_name": "What would you like to name this report?",
            "schedule_time": "When would you like to schedule this report? (e.g., 'Every Monday at 9 AM', 'Daily at 8:00')",
            "region": "Which region(s) should this report cover?",
            "date_range": "What date range should the report cover? (e.g., 'Last 30 days', 'Q1 2024')",
            "asset_types": "Which asset types should be included?",
            "delivery_method": "How would you like to receive the report? (Email, Dashboard, or Both)",
            "email_recipients": "What email address(es) should receive this report?",
            "frequency": "How often should this report run? (Daily, Weekly, Monthly)",
            "start_date": "When should the report start?",
            "description": "Would you like to add a description for this report?",
        }
        
        return questions.get(
            next_field,
            f"Please provide the value for: {next_field.replace('_', ' ').title()}"
        )
    
    def _format_dict(self, d: Dict[str, Any]) -> str:
        """Format dictionary for display"""
        if not d:
            return "  None"
        return "\n".join([f"  - {k}: {v}" for k, v in d.items()])


# Additional helper functions for validation

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


def parse_schedule_time(time_str: str) -> Dict[str, Any]:
    """
    Parse natural language time expressions into structured format
    
    Examples:
        "Every Monday at 9 AM" -> {"frequency": "weekly", "day_of_week": "monday", "time": "09:00"}
        "Daily at 8:00" -> {"frequency": "daily", "time": "08:00"}
        "First day of month" -> {"frequency": "monthly", "day_of_month": 1}
    """
    time_str = time_str.lower().strip()
    result = {}
    
    # Frequency detection
    if "daily" in time_str or "every day" in time_str:
        result["frequency"] = "daily"
    elif "weekly" in time_str or any(day in time_str for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        result["frequency"] = "weekly"
    elif "monthly" in time_str or "month" in time_str:
        result["frequency"] = "monthly"
    
    # Day of week
    days = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    for day, num in days.items():
        if day in time_str:
            result["day_of_week"] = day
            result["day_of_week_num"] = num
            break
    
    # Time extraction (basic pattern)
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',
        r'(\d{1,2})\s*(am|pm)',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else 0
            
            if len(match.groups()) > 2 and match.group(3):
                am_pm = match.group(3).lower()
                if am_pm == "pm" and hour < 12:
                    hour += 12
                elif am_pm == "am" and hour == 12:
                    hour = 0
            
            result["time"] = f"{hour:02d}:{minute:02d}"
            break
    
    return result


def parse_date_range(date_str: str) -> Dict[str, Any]:
    """
    Parse natural language date ranges
    
    Examples:
        "Last 30 days" -> {"relative": "last_30_days"}
        "Q1 2024" -> {"start": "2024-01-01", "end": "2024-03-31"}
        "January 2024" -> {"start": "2024-01-01", "end": "2024-01-31"}
    """
    date_str = date_str.lower().strip()
    result = {}
    
    # Relative dates
    if "last" in date_str:
        if "30 days" in date_str or "month" in date_str:
            result["relative"] = "last_30_days"
        elif "7 days" in date_str or "week" in date_str:
            result["relative"] = "last_7_days"
        elif "90 days" in date_str or "quarter" in date_str:
            result["relative"] = "last_90_days"
        elif "year" in date_str:
            result["relative"] = "last_year"
    
    # Quarter detection
    quarters = {"q1": (1, 3), "q2": (4, 6), "q3": (7, 9), "q4": (10, 12)}
    for q, (start_month, end_month) in quarters.items():
        if q in date_str:
            year_match = re.search(r'20\d{2}', date_str)
            if year_match:
                year = year_match.group()
                result["start"] = f"{year}-{start_month:02d}-01"
                # End date calculation would need calendar logic
                result["end"] = f"{year}-{end_month:02d}-30"
    
    return result