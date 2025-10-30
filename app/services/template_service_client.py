"""
Template Service Client

Mock implementation of template service for development/testing.
In production, replace with actual API calls to your template service.
"""

from typing import Dict, Any, List, Optional
import uuid



# Mock template database
MOCK_TEMPLATES = [
    {
        "id": "388a6a7b-1405-4fe2-b352-eb0fc6bde269",
        "name": "Demographics: Basic",
        "description": "Demographics",
        "category": "demographics",
        "config": {
            "required_fields": ["report_name", "schedule_time"],
            "optional_fields": []
        }
    },
    {
        "id": "f4d65171-986f-4ed5-b1a5-a0e1a4adf7db",
        "name": "Demographics: By Region",
        "description": "Demographics By Region",
        "category": "demographics",
        "config": {
            "required_fields": ["report_name", "schedule_time", "region"],
            "optional_fields": []
        }
    },
    {
        "id": "321f163b-e14e-46df-b0b4-593211f13c72",
        "name": "Asset: Overview",
        "description": "Asset Overview",
        "category": "asset",
        "config": {
            "required_fields": ["report_name", "schedule_time", "asset_types"],
            "optional_fields": []
        }
    },
    {
        "id": "321f163b-e14e-46df-b0b4-593211f13c72",
        "name": "Participate with incomplete checklist",
        "description": "Participate with incomplete checklist",
        "category": "incomplete_checklist",
        "config": {
            "required_fields": ["report_name", "schedule_time", "company_id", "region"],
            "optional_fields": []
        }
    }
]


def list_templates() -> List[Dict[str, Any]]:
    """Return all available templates"""
    return MOCK_TEMPLATES.copy()

