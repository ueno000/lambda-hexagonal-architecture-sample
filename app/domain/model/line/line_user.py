from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class UserStatus(Enum):
    Unregistered = 0
    PendingRegistration = 1
    Registered = 2
    Blocked = 3


class LINEUser(BaseModel):
    id: str = Field(..., title="Id")
    line_id: str = Field(..., title="LINEId")
    name: str = Field(None, title="Name")
    status: UserStatus = Field(default=UserStatus.Unregistered, title="Status")
    create_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), title="CreateDate")
    last_update_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), title="LastUpdateDate")
