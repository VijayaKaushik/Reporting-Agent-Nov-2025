"""
Template Management Tools

Provides tools for template discovery, search, and retrieval.
These tools interact with the template service to provide template information.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from app.services.template_service_client import (
    list_templates,
    search_templates_by_keyword,
    get_template_by_id,
    get_categories
)


@tool("fetch_all_templates_tool", return_direct=False)
def fetch_all_templates_tool() -> List[Dict[str, Any]]:
    """
    Retrieves the complete list of all available report templates.

    Use this tool when:
    - User wants to browse all available templates
    - User says "show me all templates" or "what reports can I create?"
    - Search returned no results and you want to show alternatives
    - User is exploring options without specific criteria

    Returns:
        A list of dictionaries, where each dictionary represents a report template.
        Each template includes:
        - id (str): Unique UUID identifier
        - name (str): Display name of the template
        - description (str): Brief description of what the template does
        - category (str): Template category (e.g., "Demographics", "Financial")
        - config (dict): Configuration including required_fields
        
    Example return:
        [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Participant Age Distribution",
                "description": "Analyzes age demographics across different regions",
                "category": "Demographics",
                "config": {
                    "required_fields": ["report_name", "schedule_time", "region"]
                }
            },
            ...
        ]
    """
    return list_templates()


@tool("search_templates_tool", return_direct=False)
def search_templates_tool(search_query: str) -> List[Dict[str, Any]]:
    """
    Searches for templates matching specific keywords or criteria.

    Use this tool when:
    - User mentions specific keywords (e.g., "demographic", "financial", "sales")
    - User asks for a specific type of report
    - User provides search criteria
    - You want to filter templates based on user intent

    Args:
        search_query: Keywords or phrases to search for in template names and descriptions.
                     Extract meaningful keywords from the user's message.
                     Examples: "demographics", "financial analysis", "participant", "sales"

    Returns:
        A filtered list of templates matching the search query.
        Returns empty list if no matches found.
        
    Example usage:
        User: "I need a report about participant demographics"
        Call: search_templates_tool("participant demographics")
        
    Example return:
        [
            {
                "id": "550e8400-...",
                "name": "Participant Demographics Summary",
                "description": "Comprehensive demographic analysis",
                "category": "Demographics",
                "match_score": 0.95
            }
        ]
    """
    if not search_query or not search_query.strip():
        return []
    
    return search_templates_by_keyword(search_query.strip())


@tool("describe_template_tool", return_direct=False)
def describe_template_tool(template_id: str) -> Dict[str, Any]:
    """
    Fetches the complete, detailed configuration for a specific report template.

    Use this tool when:
    - User asks "tell me more about template X"
    - User wants details about a specific template
    - User has selected a template and you need the full config
    - You need to retrieve required_fields for a template
    - Comparing multiple templates

    Args:
        template_id: The unique identifier (UUID string) of the report template.
                    This should be extracted from the template list shown to the user.

    Returns:
        A dictionary containing the complete template configuration:
        - id (str): Template UUID
        - name (str): Template name
        - description (str): Detailed description
        - category (str): Category classification
        - config (dict): Full configuration including:
            - required_fields (list): Fields user must provide
            - optional_fields (list): Fields user can optionally provide
            - output_format (str): Report output format
            - visualization_type (str): Chart/graph types used
            - data_sources (list): Where data comes from
            
    Returns error dict if template_id not found.
    
    Example return:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Geographic Demographics Report",
            "description": "Shows participant distribution across countries and regions with interactive maps",
            "category": "Demographics",
            "config": {
                "required_fields": [
                    "report_name",
                    "schedule_time",
                    "region"
                ],
                "optional_fields": [
                    "date_range",
                    "participant_status"
                ],
                "output_format": "PDF, Excel",
                "visualization_type": "map, bar_chart",
                "data_sources": ["participant_db", "geo_db"]
            }
        }
    """
    if not template_id or not template_id.strip():
        return {"error": "template_id is required"}
    
    template = get_template_by_id(template_id.strip())
    
    if not template:
        return {
            "error": "template not found",
            "message": f"No template exists with id: {template_id}"
        }
    
    return template


@tool("get_template_categories_tool", return_direct=False)
def get_template_categories_tool() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves all available template categories and templates within each category.

    Use this tool when:
    - User wants to browse by category
    - User asks "what types of reports are available?"
    - User says "show me financial reports" or "what demographics templates do you have?"
    - You want to organize templates for easier browsing

    Returns:
        A dictionary where keys are category names and values are lists of templates.
        
    Example return:
        {
            "Demographics": [
                {
                    "id": "550e8400-...",
                    "name": "Participant Age Distribution",
                    "description": "Age demographics analysis"
                },
                {
                    "id": "661f9511-...",
                    "name": "Geographic Demographics",
                    "description": "Location-based demographics"
                }
            ],
            "Financial": [
                {
                    "id": "772fa622-...",
                    "name": "Revenue Analysis",
                    "description": "Financial performance metrics"
                }
            ],
            "Operations": [...]
        }
    """
    return get_categories()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (Not exposed as tools)
# ═══════════════════════════════════════════════════════════════════════════

def validate_template_selection(template_id: str, available_templates: List[Dict[str, Any]]) -> bool:
    """
    Validate that a selected template_id exists in the available templates.
    
    Args:
        template_id: The UUID to validate
        available_templates: List of template dicts with 'id' field
    
    Returns:
        True if template_id is valid, False otherwise
    """
    if not template_id:
        return False
    
    valid_ids = {t.get("id") for t in available_templates if "id" in t}
    return template_id in valid_ids


def extract_template_summary(template: Dict[str, Any]) -> str:
    """
    Create a one-line summary of a template for display.
    
    Args:
        template: Template dictionary
    
    Returns:
        Formatted string like "Participant Age Distribution - Analyzes age demographics"
    """
    name = template.get("name", "Unknown Template")
    description = template.get("description", "")
    
    # Truncate description if too long
    if len(description) > 60:
        description = description[:57] + "..."
    
    return f"{name} - {description}" if description else name


def format_template_list(templates: List[Dict[str, Any]], max_items: int = 5) -> str:
    """
    Format a list of templates for display to user.
    
    Args:
        templates: List of template dictionaries
        max_items: Maximum number of templates to show
    
    Returns:
        Formatted string with numbered list
    """
    if not templates:
        return "No templates found."
    
    lines = []
    for i, template in enumerate(templates[:max_items], 1):
        summary = extract_template_summary(template)
        lines.append(f"{i}. **{summary}**")
    
    if len(templates) > max_items:
        lines.append(f"\n...and {len(templates) - max_items} more templates.")
    
    return "\n".join(lines)