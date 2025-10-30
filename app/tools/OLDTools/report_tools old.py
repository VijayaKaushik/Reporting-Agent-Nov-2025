import uuid
from typing import Dict, Any

from langchain_core.tools import tool


@tool("collect_required_fields_tool", parse_docstring=True)
def collect_required_fields_tool(template_id: str) -> Dict[str, Any]:
    """
    Retrieves the mandatory field names required for a specific report template.

    This function is essential for dynamically determining what inputs the user
    must provide before a new report can be created or scheduled.

    Args:
        template_id: The unique identifier (string) of the report template
                     for which to fetch the required field names.

    Returns:
        A dictionary containing a list of required field names under the key 'required_field'.
        Example: {"required_field": ["report_name", "schedule_time"]}
    """
    print("This is the template id", template_id)
    return {"required_field": ["report_name", "schedule_time"]}


@tool("trigger_report_tool", parse_docstring=True)
def trigger_report_tool(template_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submits a request to trigger the generation of a specific report.

    This function takes a template identifier and all necessary user inputs
    to initiate a new, asynchronous report generation job.

    Args:
        template_id: The unique identifier (uuid) of the report template
                     to be generated.
        inputs: A dictionary containing all the required fields and their values
                for the specific report, such as 'report_name' and 'schedule_time'.

    Returns:
        A dictionary containing the 'job_id' (UUID string) for the newly created
        report job and its initial 'status' (e.g., "queue").
        Example: {"job_id": "a911ac88-2284-adfd-8121-04af61282d9f", "status": "queue"}
    """
    # The actual implementation:
    print("This is the job creating stage for", template_id, inputs)
    return {"job_id": str(uuid.uuid4()), "status": "queue"}


@tool("generate_report_url_tool", parse_docstring=True)
def generate_report_url_tool(job_id: str) -> Dict[str, Any]:
    """
    Generates and retrieves the direct URL for accessing a specified, finalized report.

    This function should be called after a report job is complete to provide the
    user with the link to view their generated document.

    Args:
        job_id: The unique identifier (string) of the completed report job.

    Returns:
        A dictionary containing the report's permanent access URL under the key 'url'.
        Example: {"url": "http://dashboard.com/reports/a911ac88-2284-adfd-8121-04af61282d9f"}
    """
    print("Here is the url for report")
    return {"url": f"http://dashboard.com/reports/{job_id}"}
