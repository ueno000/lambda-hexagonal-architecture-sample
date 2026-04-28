from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CharacterType(Enum):
    Student_Female = 0
    Student_Male = 1
    Butler = 2
    Fairy = 3


class AIUserProfile(BaseModel):
    id: str = Field(..., title="Id")
    line_user_id: str = Field(..., title="LINEUserId")
    name: str = Field(default=None, title="Name")
    gender: str = Field(default=None, title="Gender")
    age: str = Field(default=None, title="Age")
    region: Optional[str] = Field(default=None, title="Region")
    region_cd: Optional[str] = Field(default=None, title="Region_Code")
    lines: Optional[List[str]] = Field(default=None, title="Lines")
    interest_topics: Optional[List[str]] = Field(default=None, title="InterestTopics")
    character_type: CharacterType = Field(
        default=CharacterType.Student_Female, title="CharacterType"
    )
