from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class UserRequestData(BaseModel):
    user_profile_id: str = Field(default=None, title="UserProfileId")
    name: str = Field(default=None, title="Name")
    gender: str = Field(default=None, title="Gender")
    age: str = Field(default=None, title="Age")
    prefecture: Optional[str] = Field(default=None, title="Prefecture")
    city: Optional[str] = Field(default=None, title="City")
    lines: List[int] = Field(default_factory=None, title="Lines")
    interest_topics: List[int] = Field(default_factory=None, title="InterestTopics")
