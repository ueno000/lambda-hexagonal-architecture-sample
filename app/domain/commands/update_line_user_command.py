from typing import Optional

from pydantic import BaseModel


class CreateLINEUserCommand(BaseModel):
    line_id: str
    name: str
    user_status: int
    last_update_date: str
