from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class ExistUserResult(BaseModel):
    is_exist: bool = Field(..., title="LINEUserId")
    user_profile_id: Optional[str] = Field(default=None, title="UserProfileId")
    name: Optional[str] = Field(default=None, title="Name")
    gender: Optional[str] = Field(default=None, title="Gender")
    age: Optional[str] = Field(default=None, title="Age")
    region: Optional[str] = Field(default=None, title="Region")
    region_cd: Optional[str] = Field(default=None, title="Region_Code")
    lines: Optional[List[int]] = Field(default_factory=None, title="Lines")
    interest_topics: Optional[List[int]] = Field(
        default_factory=None, title="InterestTopics"
    )
