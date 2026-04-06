from typing import Optional

from pydantic import BaseModel


class CreateLINEUserCommand(BaseModel):
    line_id: str
    user_status: int
    created_at: str
