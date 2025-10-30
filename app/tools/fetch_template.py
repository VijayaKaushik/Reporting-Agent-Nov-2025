from typing import Dict, Any, List
from langchain.tools import tool
from ..services.template_service_client import list_templates



@tool("fetch_template_tool", return_direct=False, parse_docstring=True)
def fetch_template_tool() -> List[Dict[str, Any]]:
    """
    Retrieves a list of all available report templates, including their names and unique IDs.

    This function provides the complete catalogue of reports that the system can generate,
    allowing the user or agent to select a template for further action (like describing or triggering).

    Args:
        # No arguments are required for this tool.

    Returns:
        A list of dictionaries, where each dictionary represents a report template.
        Each entry includes the 'id', 'name', and 'config' keys.
        Example: [{"id": "...", "name": "...", "config": {...}}, ...]
    """
    return list_templates()


@tool("describe_template_tool", return_direct=False, parse_docstring=True)
def describe_template_tool(template_id: str) -> Dict[str, Any]:
    """
    Fetches the detailed configuration for a specific report template, including all required input fields.

    The main purpose of this tool is to retrieve the necessary parameters (e.g., 'region', 'asset_types')
    that a user must supply to successfully generate a report using the given template ID.

    Args:
        template_id: The unique identifier (string, a UUID) of the report template
                     whose full configuration details are required.

    Returns:
        A dictionary containing the full template configuration, including the
        'required_fields' list within the 'config' key. Returns a simple error
        dictionary if the ID is not found.
        Example: {"id": "...", "name": "...", "config": {"required_fields": ["report_name", "schedule_time", "region"]}}
    """
    templates = list_templates()
    for t in templates:
        if t["id"] == template_id:
            return t
    return {"error": "template not found"}