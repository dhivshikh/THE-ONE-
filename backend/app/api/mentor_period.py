from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.db.models import MentorPeriod

router = APIRouter(prefix="/mentor-period", tags=["Mentor Period"])

class MentorPeriodSettings(BaseModel):
    is_enabled: bool
    departments: Optional[List[int]] = None
    years: Optional[List[int]] = None
    classes: Optional[List[int]] = None

class MentorPeriodResponse(MentorPeriodSettings):
    id: int
    is_scheduled: bool
    scheduled_day: Optional[int]
    scheduled_slot: Optional[int]

@router.get("", response_model=MentorPeriodResponse)
def get_mentor_period_settings(db: Session = Depends(get_db)):
    """Get the current Mentor Period configuration."""
    setting = db.query(MentorPeriod).first()
    if not setting:
        # Create default
        setting = MentorPeriod(is_enabled=False)
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return {
        "id": setting.id,
        "is_enabled": setting.is_enabled,
        "departments": [int(x) for x in setting.departments.split(',')] if setting.departments else [],
        "years": [int(x) for x in setting.years.split(',')] if setting.years else [],
        "classes": [int(x) for x in setting.classes.split(',')] if setting.classes else [],
        "is_scheduled": setting.is_scheduled,
        "scheduled_day": setting.scheduled_day,
        "scheduled_slot": setting.scheduled_slot,
    }

@router.post("", response_model=MentorPeriodResponse)
def update_mentor_period_settings(data: MentorPeriodSettings, db: Session = Depends(get_db)):
    """Update Mentor Period configuration."""
    setting = db.query(MentorPeriod).first()
    if not setting:
        setting = MentorPeriod()
        db.add(setting)

    setting.is_enabled = data.is_enabled
    setting.departments = ",".join(map(str, data.departments)) if data.departments else None
    setting.years = ",".join(map(str, data.years)) if data.years else None
    setting.classes = ",".join(map(str, data.classes)) if data.classes else None

    # Reset scheduling status when config changes
    setting.is_scheduled = False
    setting.scheduled_day = None
    setting.scheduled_slot = None

    db.commit()
    db.refresh(setting)

    return {
        "id": setting.id,
        "is_enabled": setting.is_enabled,
        "departments": [int(x) for x in setting.departments.split(',')] if setting.departments else [],
        "years": [int(x) for x in setting.years.split(',')] if setting.years else [],
        "classes": [int(x) for x in setting.classes.split(',')] if setting.classes else [],
        "is_scheduled": setting.is_scheduled,
        "scheduled_day": setting.scheduled_day,
        "scheduled_slot": setting.scheduled_slot,
    }
