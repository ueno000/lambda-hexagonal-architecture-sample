from typing import List, Optional

from pydantic import BaseModel, Field


class AIUserProfile(BaseModel):
    id: str = Field(..., title="Id")
    line_user_id: str = Field(..., title="LINEUserId")
    name: Optional[str] = Field(default=None, title="Name")
    gender: Optional[str] = Field(default=None, title="Gender")
    birth_year: Optional[int] = Field(default=None, title="BirthYear")
    interest_topics: List[str] = Field(default_factory=list, title="InterestTopics")
    residence: Optional[str] = Field(default=None, title="Residence")
    lines: List[str] = Field(default_factory=list, title="Lines")
