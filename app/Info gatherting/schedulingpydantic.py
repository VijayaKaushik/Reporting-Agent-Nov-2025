from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ReportScheduleRequest(BaseModel):
    template_id: int = Field(..., description="ID of the report template to schedule")
    schedule_name: str = Field(..., description="Name of the scheduled report")
    frequency: str = Field(..., description="Schedule frequency: once, daily, weekly, monthly")
    run_date: Optional[datetime] = Field(None, description="Run date if frequency is 'once'")
    start_date: Optional[datetime] = Field(None, description="Start date if recurring")
    end_date: Optional[datetime] = Field(None, description="End date for recurring schedule")

    @field_validator("frequency")
    def validate_frequency(cls, v):
        allowed = {"once", "daily", "weekly", "monthly"}
        if v.lower() not in allowed:
            raise ValueError(f"Frequency must be one of {allowed}")
        return v.lower()

    @field_validator("run_date", always=True)
    def validate_run_or_start_date(cls, v, values):
        freq = values.get("frequency")
        start = values.get("start_date")
        if freq == "once" and not v:
            raise ValueError("run_date must be provided when frequency is 'once'")
        if freq != "once" and not start:
            raise ValueError("start_date must be provided for recurring schedules")
        return v
