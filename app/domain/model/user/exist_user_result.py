from typing import List, Optional

from pydantic import BaseModel, Field


class ExistUserResult(BaseModel):
    is_exist: bool = Field(..., title="IsExist")
    user_profile_id: Optional[str] = Field(default=None, title="UserProfileId")
    name: Optional[str] = Field(default=None, title="Name")
    gender: Optional[str] = Field(default=None, title="Gender")
    age: Optional[str] = Field(default=None, title="Age")
    region: Optional[str] = Field(default=None, title="Region")
    region_cd: Optional[str] = Field(default=None, title="Region_Code")
    lines: Optional[List[str]] = Field(default=None, title="Lines")
    interest_topics: Optional[List[str]] = Field(default=None, title="InterestTopics")
