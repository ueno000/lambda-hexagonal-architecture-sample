from app.domain.model.line.line_messaging_webhook_event import LINEMessageEvent
from app.domain.model.line.line_user import LINEUser
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Any, Optional, List
from enum import Enum
from dataclasses import dataclass


class ChatSession(BaseModel):
    id: str = Field(..., title="Id")
    ai_user_profile_id: Optional[str] = None
    reply_message: Optional[str] = None
    ai_response: Optional["AIResponse"] = None
    create_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        title="CreateDate",
    )
    last_update_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        title="LastUpdateDate",
    )


@dataclass
class WeatherPeriod:
    description: Optional[str] = None
    temperature: Optional[str] = None
    rain: Optional[str] = None
    umbrella: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class Weather:
    today_to_daytime: Optional[WeatherPeriod] = None
    daytime_to_night: Optional[WeatherPeriod] = None


@dataclass
class Train:
    line: Optional[str] = None
    status: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class News:
    title: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class Topic:
    type: Optional[str] = None
    title: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class AIResponse:
    timestamp: Optional[str] = None
    weather: Optional[Weather] = None
    train: Optional[List[Train]] = None
    news: Optional[List[News]] = None
    topics: Optional[List[Topic]] = None
    message: Optional[str] = None
