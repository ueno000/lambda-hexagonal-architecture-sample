from typing import List, Optional

from pydantic import BaseModel, Field


class AIUserProfile(BaseModel):
    id: str = Field(..., title="Id")
    line_user_id: str = Field(..., title="LINEUserId")
    name: str = Field(default=None, title="Name")
    gender: str = Field(default=None, title="Gender")
    age: str = Field(default=None, title="Age")
    region: Optional[str] = Field(default=None, title="Region")
    region_cd: Optional[str] = Field(default=None, title="Region_Code")
    lines: List[int] = Field(default_factory=None, title="Lines")
    interest_topics: List[int] = Field(default_factory=None, title="InterestTopics")
