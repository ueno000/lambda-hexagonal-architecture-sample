from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AIUserProfileRequestBase(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

    @field_validator("name")
    def validate_name(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError("nameの文字数が10文字を超えています。")
        return v

    gender: Optional[str] = None
    age: Optional[str] = None
    region: Optional[str] = None
    region_cd: Optional[str] = None
    lines: Optional[List[str]] = None
    interest_topics: Optional[List[str]] = None


class AIUserProfileRequestCreate(AIUserProfileRequestBase):
    line_user_id: str
    name: str
    gender: str
    age: str


class AIUserProfileRequestUpdate(AIUserProfileRequestBase):
    class Config:
        extra = "forbid"
