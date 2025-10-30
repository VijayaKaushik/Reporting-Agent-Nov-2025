"""
State Management for Multi-Agent Report Generation System

State Dictionary Schema:
{
    # Session context
    "thread_id": str,                          # Conversation identifier
    "user_message": str,                       # Latest user input
    "conversation_history": List[Dict],        # (Optional) Message history
    
    # Template management
    "selected_template_id": Optional[str],     # UUID of chosen template
    "template_config": Dict[str, Any],         # Full template configuration
    "template_search_results": List[Dict],     # Available templates
    
    # Input collection
    "provided_inputs": Dict[str, Any],         # User-supplied field values
    "missing_fields": List[str],               # Fields still needed
    
    # Scheduling
    "job_id": Optional[str],                   # Scheduled report job UUID
    "report_url": Optional[str],               # Dashboard URL for report
    
    # Flow control
    "workflow_stage": str,                     # discovery|selection|input_collection|scheduling
    "next_agent": str,                         # Router's decision
    "template_next_step": Optional[str],       # Template/collector transition
    "reply": str,                              # Bot's response message
    
    # Debugging
    "routing_reason": Optional[str]            # (Optional) Why router chose this path
}
"""

from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict, total=False):
    """
    Complete state schema for the report generation workflow.
    All fields are optional (total=False) to allow incremental state building.
    """
    
    # Session context
    thread_id: str
    user_message: str
    conversation_history: Optional[List[Dict[str, str]]]
    
    # Template management
    selected_template_id: Optional[str]
    template_config: Dict[str, Any]
    template_search_results: List[Dict[str, Any]]
    
    # Input collection
    provided_inputs: Dict[str, Any]
    missing_fields: List[str]
    
    # Scheduling
    job_id: Optional[str]
    report_url: Optional[str]
    
    # Flow control
    workflow_stage: str
    next_agent: str
    template_next_step: Optional[str]
    reply: str
    
    # Debugging
    routing_reason: Optional[str]