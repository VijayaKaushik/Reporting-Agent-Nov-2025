from typing import TypedDict, List, Dict, Any

class GraphState(TypedDict):

    thread_id: str # this use to store your information in checkpointer
    user_message: str
    messages: List[Dict[str, str]] # [ {}, {}, {}]

    # intent
    intent: str # create_report, view_status, unknow

    # template
    candidate_templates: List[Dict[str, Any]]
    selected_template_id: str

    # input
    required_fields: List[str]
    provided_inputs: Dict[str, Any]
    missing_fields: List[str]

    # reporting
    job_id: str
    result_url: str

    # control/stats
    status: str # need_template_choice | need_inputs | running | done | error
    reply: str