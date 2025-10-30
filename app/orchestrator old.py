"""
Multi-Agent Report Generation Orchestrator

Workflow:
        START
          |
     ROUTING_AGENT
     /      |      \
TEMPLATE  USER_INPUT  SCHEDULING
 AGENT    COLLECTOR    AGENT
    \        |        /
     \       |       /
      \      |      /
         END

Flow Description:
1. User request → routing_agent analyzes intent and state
2. Routes to template_agent for discovery/selection
3. Routes to user_input_collector for gathering required fields
4. Routes to scheduling_agent when all data is ready
5. Agents can loop back through routing for multi-step workflows
"""

from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.registry import init_agents, get_agent


# Initialize checkpointer for session state persistence
checkpointer = MemorySaver()


def build_graph() -> StateGraph:
    """
    Constructs the multi-agent workflow graph with conditional routing.
    
    Returns:
        Compiled StateGraph with checkpointing enabled
    """
    # Initialize all agents in the registry
    init_agents()
    
    # Create state graph with dict-based state
    graph = StateGraph(dict)
    
    # ═══════════════════════════════════════════════════════════════════
    # NODE DEFINITIONS
    # ═══════════════════════════════════════════════════════════════════
    
    # Central routing agent - analyzes state and directs flow
    graph.add_node(
        "routing_agent",
        lambda state: get_agent("routing_agent").execute(state)
    )
    
    # Template discovery and selection agent
    graph.add_node(
        "template_agent",
        lambda state: get_agent("template_agent").execute(state)
    )
    
    # User input collection agent - gathers required fields
    graph.add_node(
        "user_input_collector",
        lambda state: get_agent("user_input_collector").execute(state)
    )
    
    # Scheduling and report triggering agent
    graph.add_node(
        "scheduling_agent",
        lambda state: get_agent("scheduling_agent").execute(state)
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # EDGE DEFINITIONS
    # ═══════════════════════════════════════════════════════════════════
    
    # Entry point: all requests start with routing
    graph.add_edge(START, "routing_agent")
    
    # Routing agent decides next agent based on state
    graph.add_conditional_edges(
        source="routing_agent",
        path=lambda state: state.get("next_agent", "template_agent"),
        path_map={
            "template_agent": "template_agent",
            "user_input_collector": "user_input_collector",
            "scheduling_agent": "scheduling_agent"
        }
    )
    
    # Template agent can transition to:
    # - user_input_collector (when template selected, needs fields)
    # - routing_agent (for re-evaluation)
    # - END (if handling a simple query)
    graph.add_conditional_edges(
        source="template_agent",
        path=lambda state: state.get("template_next_step", "end"),
        path_map={
            "user_input_collector": "user_input_collector",
            "routing_agent": "routing_agent",
            "scheduling_agent": "scheduling_agent",
            "end": END
        }
    )
    
    # User input collector can transition to:
    # - user_input_collector (loop back for more fields)
    # - scheduling_agent (all fields collected)
    # - routing_agent (user changes mind)
    graph.add_conditional_edges(
        source="user_input_collector",
        path=lambda state: state.get("template_next_step", "user_input_collector"),
        path_map={
            "user_input_collector": "user_input_collector",
            "scheduling_agent": "scheduling_agent",
            "routing_agent": "routing_agent"
        }
    )
    
    # Scheduling agent is terminal - always goes to END
    graph.add_edge("scheduling_agent", END)
    
    # ═══════════════════════════════════════════════════════════════════
    # COMPILE GRAPH
    # ═══════════════════════════════════════════════════════════════════
    
    return graph.compile(checkpointer=checkpointer)


# Global graph instance
graph = build_graph()


def run_graph(thread_id: str, user_message: str, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute the graph for a given user message within a conversation thread.
    
    Args:
        thread_id: Unique identifier for the conversation session
        user_message: The user's natural language input
        previous_state: Optional previous state to continue conversation
    
    Returns:
        Final state dictionary containing:
        - reply: Bot's response to the user
        - selected_template_id: Selected template (if any)
        - provided_inputs: Collected field values
        - job_id: Scheduled report job ID (if completed)
        - workflow_stage: Current stage in the workflow
    
    Example:
        >>> result = run_graph("user-123", "I want a demographics report")
        >>> print(result["reply"])
        "I found 3 templates for demographics. Which would you like?"
    """
    
    # Configure with thread-specific checkpointing
    config = RunnableConfig(
        configurable={"thread_id": thread_id}
    )
    
    # Try to get previous state from checkpointer if available
    if previous_state is None:
        try:
            # Attempt to retrieve the last state for this thread
            state_snapshot = graph.get_state(config)
            previous_state = state_snapshot.values if state_snapshot else {}
        except Exception:
            # If no previous state exists, start fresh
            previous_state = {}
    
    # Initialize state with user message and preserve existing context
    state: Dict[str, Any] = {
        # Session context
        "thread_id": thread_id,
        "user_message": user_message,
        
        # Preserve existing state values or set defaults
        "workflow_stage": previous_state.get("workflow_stage", "discovery"),
        "selected_template_id": previous_state.get("selected_template_id"),
        "template_config": previous_state.get("template_config", {}),
        "template_search_results": previous_state.get("template_search_results", []),
        "provided_inputs": previous_state.get("provided_inputs", {}),
        "missing_fields": previous_state.get("missing_fields", []),
        
        # Flow control
        "next_agent": None,
        "template_next_step": None,
        "reply": "",
        
        # Job tracking
        "job_id": previous_state.get("job_id"),
        "report_url": previous_state.get("report_url"),
        
        # Optional fields
        "conversation_history": previous_state.get("conversation_history", []),
        "routing_reason": None
    }
    
    # Execute the graph
    final_state = graph.invoke(state, config=config)
    
    # Optional: Retrieve state history for debugging/analytics
    # states_history = list(graph.get_state_history(config))
    # for historical_state in states_history:
    #     print(f"Checkpoint: {historical_state.config['configurable']['checkpoint_id']}")
    #     print(f"Next: {historical_state.next}")
    #     print(f"Values: {historical_state.values}")
    
    return final_state


def get_conversation_history(thread_id: str) -> list:
    """
    Retrieve the complete state history for a conversation thread.
    
    Args:
        thread_id: The conversation thread identifier
    
    Returns:
        List of state snapshots in chronological order
    """
    config = RunnableConfig(
        configurable={"thread_id": thread_id}
    )
    try:
        return list(graph.get_state_history(config))
    except Exception as e:
        print(f"Error retrieving conversation history: {e}")
        return []


def get_current_state(thread_id: str) -> Dict[str, Any]:
    """
    Get the current state for a conversation thread.
    
    Args:
        thread_id: The conversation thread identifier
    
    Returns:
        Current state dictionary or empty dict if not found
    """
    config = RunnableConfig(
        configurable={"thread_id": thread_id}
    )
    try:
        state_snapshot = graph.get_state(config)
        return state_snapshot.values if state_snapshot else {}
    except Exception as e:
        print(f"Error retrieving current state: {e}")
        return {}


def reset_conversation(thread_id: str) -> None:
    """
    Clear the state history for a conversation thread.
    
    Args:
        thread_id: The conversation thread to reset
    """
    # Note: MemorySaver doesn't have explicit clear method
    # State will be overwritten on next invocation
    # For production, implement proper state cleanup
    config = RunnableConfig(
        configurable={"thread_id": thread_id}
    )
    
    # Initialize with empty state to effectively reset
    empty_state = {
        "thread_id": thread_id,
        "user_message": "",
        "workflow_stage": "discovery",
        "selected_template_id": None,
        "template_config": {},
        "provided_inputs": {},
        "missing_fields": [],
        "reply": "Conversation reset."
    }
    
    try:
        graph.invoke(empty_state, config=config)
        print(f"✅ Reset conversation for thread: {thread_id}")
    except Exception as e:
        print(f"⚠️ Error resetting conversation: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def continue_conversation(thread_id: str, user_message: str) -> Dict[str, Any]:
    """
    Continue an existing conversation with state preservation.
    
    Args:
        thread_id: The conversation thread identifier
        user_message: The user's new message
    
    Returns:
        Updated state with bot's response
    """
    # Get current state
    current_state = get_current_state(thread_id)
    
    # Run graph with preserved state
    return run_graph(thread_id, user_message, previous_state=current_state)


def start_new_conversation(thread_id: str, user_message: str) -> Dict[str, Any]:
    """
    Start a fresh conversation, ignoring any previous state.
    
    Args:
        thread_id: The conversation thread identifier
        user_message: The user's initial message
    
    Returns:
        New state with bot's response
    """
    return run_graph(thread_id, user_message, previous_state=None)


# ═══════════════════════════════════════════════════════════════════════════
# STATE SCHEMA DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════

"""
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