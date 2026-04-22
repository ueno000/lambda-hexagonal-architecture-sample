from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class UserProfileRequest(BaseModel):
    user_profile_id: str = Field(default=None, title="UserProfileId")
    name: str = Field(default=None, title="Name")
    gender: str = Field(default=None, title="Gender")
    age: str = Field(default=None, title="Age")
    regin: Optional[str] = Field(default=None, title="Regin")
    regin_cd: Optional[str] = Field(default=None, title="Regin_Code")
    lines: Optional[List[int]] = Field(default_factory=None, title="Lines")
    interest_topics: Optional[List[int]] = Field(
        default_factory=None, title="InterestTopics"
    )
