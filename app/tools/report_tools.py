"""
Report Scheduling and Management Tools

Provides comprehensive tools for:
- Input validation
- Job triggering (one-time and recurring)
- Status tracking
- Report management
- URL generation
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool


@tool("validate_report_inputs_tool")
def validate_report_inputs_tool(template_id: str, provided_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates that all required fields for a template have been provided.

    ⚠️ CRITICAL: Always call this tool BEFORE triggering any report job.
    This ensures data completeness and prevents job failures.

    Use this tool when:
    - About to trigger a report job
    - User says "schedule it" or "run it"
    - Before calling trigger_report_job_tool or schedule_recurring_report_tool
    - Anytime you need to verify completeness

    Args:
        template_id: The UUID of the selected report template
        provided_inputs: Dictionary of field values collected from the user
                        Example: {"report_name": "Weekly Report", "schedule_time": "...", "region": "NA"}

    Returns:
        Dictionary containing:
        - is_valid (bool): True if all required fields are present
        - missing_fields (list): List of field names still needed (empty if valid)
        - validation_message (str): Human-readable validation result
        - ready_to_schedule (bool): True if can proceed to scheduling

    Example return (validation passed):
        {
            "is_valid": True,
            "missing_fields": [],
            "validation_message": "All required fields are present",
            "ready_to_schedule": True
        }

    Example return (validation failed):
        {
            "is_valid": False,
            "missing_fields": ["region", "date_range"],
            "validation_message": "Missing required fields: region, date_range",
            "ready_to_schedule": False
        }
    """
    # Mock required fields lookup (in production, fetch from template service)
    required_fields_map = {
        "550e8400-e29b-41d4-a716-446655440000": ["report_name", "schedule_time", "region"],
        "661f9511-f3ac-42e5-b827-557766551111": ["report_name", "schedule_time"],
        "772fa622-g4bd-53f6-c938-668877662222": ["report_name", "schedule_time", "plan_types"],
    }
    
    required_fields = required_fields_map.get(template_id, ["report_name", "schedule_time"])
    
    # Check which fields are missing
    missing_fields = []
    for field in required_fields:
        if field not in provided_inputs or not provided_inputs[field]:
            missing_fields.append(field)
    
    is_valid = len(missing_fields) == 0
    
    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "validation_message": (
            "✓ All required fields are present" if is_valid
            else f"Missing required fields: {', '.join(missing_fields)}"
        ),
        "ready_to_schedule": is_valid
    }


@tool("trigger_report_job_tool")
def trigger_report_job_tool(
    template_id: str,
    inputs: Dict[str, Any],
    execution_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Triggers a one-time report generation job (immediate or scheduled for future).

    Use this tool when:
    - User wants to run a report once (not recurring)
    - User says "run it now", "schedule for tomorrow", "generate this report"
    - One-time execution is needed
    - After validation passes

    Args:
        template_id: The UUID of the report template to execute
        inputs: Dictionary containing all required field values
                Example: {
                    "report_name": "Q1 Demographics Report",
                    "schedule_time": "2024-01-15T09:00:00Z",
                    "region": "North America"
                }
        execution_time: (Optional) ISO format datetime for scheduled execution.
                       If None, executes immediately.
                       Example: "2024-01-15T09:00:00Z"

    Returns:
        Dictionary containing:
        - job_id (str): Unique identifier for the job
        - status (str): Current status (queued, running, scheduled)
        - execution_time (str): When job will run
        - estimated_completion (str): Expected completion time
        - template_name (str): Name of template being executed

    Example return (immediate):
        {
            "job_id": "job-a911ac88-2284-adfd-8121-04af61282d9f",
            "status": "running",
            "execution_time": "2024-01-10T14:30:00Z",
            "estimated_completion": "2024-01-10T14:45:00Z",
            "template_name": "Geographic Demographics Report"
        }

    Example return (scheduled):
        {
            "job_id": "job-b922bd99-3395-beef-9232-15bg72393e0g",
            "status": "scheduled",
            "execution_time": "2024-01-15T09:00:00Z",
            "estimated_completion": "2024-01-15T09:15:00Z",
            "template_name": "Revenue Analysis Report"
        }
    """
    job_id = f"job-{str(uuid.uuid4())}"
    
    # Determine execution time
    if execution_time:
        exec_time = execution_time
        status = "scheduled"
        estimated_completion = datetime.fromisoformat(execution_time.replace('Z', '+00:00')) + timedelta(minutes=15)
        estimated_completion_str = estimated_completion.isoformat()
    else:
        exec_time = datetime.utcnow().isoformat() + "Z"
        status = "running"
        estimated_completion_str = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"
    
    # Mock template name lookup
    template_names = {
        "550e8400-e29b-41d4-a716-446655440000": "Participant Age Distribution",
        "661f9511-f3ac-42e5-b827-557766551111": "Geographic Demographics Report",
    }
    template_name = template_names.get(template_id, "Report")
    
    print(f"🚀 Creating one-time report job for template: {template_id}")
    print(f"   Job ID: {job_id}")
    print(f"   Inputs: {inputs}")
    print(f"   Execution: {exec_time}")
    
    return {
        "job_id": job_id,
        "status": status,
        "execution_time": exec_time,
        "estimated_completion": estimated_completion_str,
        "template_name": template_name
    }


@tool("schedule_recurring_report_tool")
def schedule_recurring_report_tool(
    template_id: str,
    inputs: Dict[str, Any],
    schedule_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a recurring report schedule (daily, weekly, monthly).

    Use this tool when:
    - User wants automated recurring reports
    - User says "every Monday", "daily at 9 AM", "monthly report"
    - Ongoing scheduled execution is needed
    - After validation passes

    Args:
        template_id: The UUID of the report template to execute
        inputs: Dictionary containing all required field values
        schedule_config: Scheduling configuration containing:
                        - frequency: "daily" | "weekly" | "monthly"
                        - time: "HH:MM" (24-hour format)
                        - day_of_week: (for weekly) 0-6 where 0=Monday
                        - day_of_month: (for monthly) 1-31
                        - timezone: (optional) default "UTC"
                        
                        Example: {
                            "frequency": "weekly",
                            "day_of_week": 0,  # Monday
                            "time": "09:00",
                            "timezone": "UTC"
                        }

    Returns:
        Dictionary containing:
        - schedule_id (str): Unique identifier for the schedule
        - job_id (str): ID of the first scheduled job
        - status (str): "active"
        - next_run_time (str): ISO datetime of next execution
        - frequency (str): Schedule frequency
        - schedule_summary (str): Human-readable schedule description

    Example return:
        {
            "schedule_id": "sched-c033ce00-4406-cggh-0343-26ch83404f1h",
            "job_id": "job-d144df11-5517-diii-1454-37di94515g2i",
            "status": "active",
            "next_run_time": "2024-01-15T09:00:00Z",
            "frequency": "weekly",
            "schedule_summary": "Every Monday at 09:00 UTC"
        }
    """
    schedule_id = f"sched-{str(uuid.uuid4())}"
    job_id = f"job-{str(uuid.uuid4())}"
    
    frequency = schedule_config.get("frequency", "weekly")
    time = schedule_config.get("time", "09:00")
    timezone = schedule_config.get("timezone", "UTC")
    
    # Generate human-readable summary
    if frequency == "daily":
        summary = f"Daily at {time} {timezone}"
    elif frequency == "weekly":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_of_week = schedule_config.get("day_of_week", 0)
        summary = f"Every {days[day_of_week]} at {time} {timezone}"
    elif frequency == "monthly":
        day_of_month = schedule_config.get("day_of_month", 1)
        suffix = "th" if 11 <= day_of_month <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day_of_month % 10, "th")
        summary = f"Monthly on the {day_of_month}{suffix} at {time} {timezone}"
    else:
        summary = f"{frequency.capitalize()} at {time} {timezone}"
    
    # Calculate next run time (simplified)
    next_run = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=int(time.split(':')[0]),
        minute=int(time.split(':')[1]),
        second=0,
        microsecond=0
    ).isoformat() + "Z"
    
    print(f"📅 Creating recurring report schedule for template: {template_id}")
    print(f"   Schedule ID: {schedule_id}")
    print(f"   First Job ID: {job_id}")
    print(f"   Schedule: {summary}")
    print(f"   Inputs: {inputs}")
    
    return {
        "schedule_id": schedule_id,
        "job_id": job_id,
        "status": "active",
        "next_run_time": next_run,
        "frequency": frequency,
        "schedule_summary": summary
    }


@tool("get_report_status_tool")
def get_report_status_tool(job_id: str) -> Dict[str, Any]:
    """
    Retrieves the current status and progress of a report generation job.

    Use this tool when:
    - User asks "is my report ready?", "what's the status?", "how's it going?"
    - User wants to check progress
    - Need to determine if report is complete

    Args:
        job_id: The unique identifier of the job to check

    Returns:
        Dictionary containing:
        - job_id (str): The job identifier
        - status (str): queued | running | completed | failed
        - progress_percentage (int): 0-100 showing completion
        - current_step (str): Description of current processing step
        - estimated_completion (str): ISO datetime (if still running)
        - download_url (str): Direct download link (if completed)
        - error_message (str): Error details (if failed)

    Example return (running):
        {
            "job_id": "job-123",
            "status": "running",
            "progress_percentage": 65,
            "current_step": "Generating visualizations",
            "estimated_completion": "2024-01-10T14:35:00Z"
        }

    Example return (completed):
        {
            "job_id": "job-123",
            "status": "completed",
            "progress_percentage": 100,
            "current_step": "Complete",
            "download_url": "https://reports.example.com/download/job-123"
        }
    """
    # Mock status (in production, query job service)
    statuses = ["queued", "running", "completed"]
    import random
    status = random.choice(statuses)
    
    if status == "completed":
        return {
            "job_id": job_id,
            "status": "completed",
            "progress_percentage": 100,
            "current_step": "Complete",
            "download_url": f"https://reports.example.com/download/{job_id}",
            "completed_at": datetime.utcnow().isoformat() + "Z"
        }
    elif status == "running":
        return {
            "job_id": job_id,
            "status": "running",
            "progress_percentage": 65,
            "current_step": "Generating visualizations",
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"
        }
    else:
        return {
            "job_id": job_id,
            "status": "queued",
            "progress_percentage": 0,
            "current_step": "Waiting in queue",
            "estimated_start": (datetime.utcnow() + timedelta(minutes=2)).isoformat() + "Z"
        }


@tool("generate_report_dashboard_url_tool")
def generate_report_dashboard_url_tool(job_id: str) -> Dict[str, Any]:
    """
    Generates the dashboard URL where users can track and access their report.

    Use this tool when:
    - A job has been successfully created
    - User needs tracking information
    - Always after trigger_report_job_tool or schedule_recurring_report_tool

    Args:
        job_id: The unique identifier of the job or schedule

    Returns:
        Dictionary containing:
        - dashboard_url (str): Full URL to the tracking dashboard
        - direct_link (str): Short link for easy sharing
        - qr_code_url (str): URL to QR code for mobile access

    Example return:
        {
            "dashboard_url": "https://dashboard.example.com/reports/job-a911ac88-2284-adfd-8121-04af61282d9f",
            "direct_link": "https://rpt.ex/a911ac88",
            "qr_code_url": "https://dashboard.example.com/qr/job-a911ac88"
        }
    """
    base_url = "https://dashboard.example.com"
    
    return {
        "dashboard_url": f"{base_url}/reports/{job_id}",
        "direct_link": f"https://rpt.ex/{job_id[:8]}",
        "qr_code_url": f"{base_url}/qr/{job_id}"
    }


@tool("cancel_report_job_tool")
def cancel_report_job_tool(job_id: str) -> Dict[str, Any]:
    """
    Cancels a pending or running report job.

    Use this tool when:
    - User says "cancel my report", "stop the job", "never mind"
    - User wants to stop a scheduled job
    - Job needs to be terminated

    Args:
        job_id: The unique identifier of the job to cancel

    Returns:
        Dictionary containing:
        - job_id (str): The job identifier
        - cancellation_status (str): success | failed
        - message (str): Human-readable result
        - cancelled_at (str): ISO datetime of cancellation

    Example return:
        {
            "job_id": "job-123",
            "cancellation_status": "success",
            "message": "Report job cancelled successfully",
            "cancelled_at": "2024-01-10T14:30:00Z"
        }
    """
    print(f"🛑 Cancelling job: {job_id}")
    
    return {
        "job_id": job_id,
        "cancellation_status": "success",
        "message": "Report job cancelled successfully",
        "cancelled_at": datetime.utcnow().isoformat() + "Z"
    }


@tool("list_user_reports_tool")
def list_user_reports_tool(
    status_filter: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Lists all reports (jobs and schedules) for the current user.

    Use this tool when:
    - User asks "show my reports", "what reports do I have?", "list my jobs"
    - User wants to see report history
    - Managing multiple reports

    Args:
        status_filter: (Optional) Filter by status: "active" | "completed" | "scheduled" | "failed"
        limit: Maximum number of reports to return (default 10)

    Returns:
        Dictionary containing:
        - total_count (int): Total number of reports
        - reports (list): List of report objects
        - schedules (list): List of active recurring schedules

    Example return:
        {
            "total_count": 5,
            "reports": [
                {
                    "job_id": "job-123",
                    "template_name": "Demographics Report",
                    "status": "completed",
                    "created_at": "2024-01-10T10:00:00Z",
                    "download_url": "https://..."
                },
                ...
            ],
            "schedules": [
                {
                    "schedule_id": "sched-456",
                    "template_name": "Weekly Sales",
                    "frequency": "weekly",
                    "next_run": "2024-01-15T09:00:00Z"
                }
            ]
        }
    """
    # Mock data
    reports = [
        {
            "job_id": "job-abc123",
            "template_name": "Geographic Demographics Report",
            "status": "completed",
            "created_at": "2024-01-10T10:00:00Z",
            "download_url": "https://reports.example.com/download/job-abc123"
        },
        {
            "job_id": "job-def456",
            "template_name": "Revenue Analysis",
            "status": "running",
            "created_at": "2024-01-10T14:00:00Z",
            "progress": 75
        }
    ]
    
    schedules = [
        {
            "schedule_id": "sched-xyz789",
            "template_name": "Weekly Demographics",
            "frequency": "weekly",
            "schedule_summary": "Every Monday at 09:00 UTC",
            "next_run": "2024-01-15T09:00:00Z",
            "status": "active"
        }
    ]
    
    if status_filter:
        reports = [r for r in reports if r["status"] == status_filter]
    
    return {
        "total_count": len(reports) + len(schedules),
        "reports": reports[:limit],
        "schedules": schedules
    }