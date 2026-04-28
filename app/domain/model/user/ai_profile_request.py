from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.domain.model.ai_chat.ai_user_profile import CharacterType


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


class AIUserProfileCharacterTypeUpdateRequest(BaseModel):
    id: str = Field(..., min_length=1)
    character_type: int = Field(...)

    @field_validator("character_type", mode="before")
    def validate_character_type_is_int(cls, v):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError("character_typeは数値で指定してください。")
        return v

    @field_validator("character_type")
    def validate_character_type_range(cls, v):
        valid_values = {character_type.value for character_type in CharacterType}
        if v not in valid_values:
            raise ValueError("character_typeが不正です。")
        return v
