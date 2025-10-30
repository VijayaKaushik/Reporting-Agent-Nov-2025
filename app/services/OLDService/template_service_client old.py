from typing import List, Dict, Any

def list_templates() -> List[Dict[str, Any]]:
    # Fake data ideally should come from DB
    return [
        {
            "id": "388a6a7b-1405-4fe2-b352-eb0fc6bde269",
            "name": "Demographics: Basic",
            "config": {
                "category": "demographics",
                "description": "Demographics",
                "required_fields": ["report_name", "schedule_time"]
            }
        },
        {
            "id": "f4d65171-986f-4ed5-b1a5-a0e1a4adf7db",
            "name": "Demographics: By Region",
            "config": {
                "category": "demographics",
                "description": "Demographics By Region",
                "required_fields": ["report_name", "schedule_time", "region"]
            }
        },
        {
            "id": "321f163b-e14e-46df-b0b4-593211f13c72",
            "name": "Asset: Overview",
            "config": {
                "category": "asset",
                "description": "Asset Overview",
                "required_fields": ["report_name", "schedule_time", "asset_types"]
            }
        },
        {
            "id": "321f163b-e14e-46df-b0b4-593211f13c72",
            "name": "Participate with incomplete checklist",
            "config": {
                "category": "incomplete_checklist",
                "description": "Participate with incomplete checklist",
                "required_fields": ["report_name", "schedule_time", "company_id", "region"]
            }
        }
    ]