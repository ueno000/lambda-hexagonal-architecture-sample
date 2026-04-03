from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


# ===== Enums =====


class EventType(str, Enum):
    MESSAGE = "message"
    UNSEND = "unsend"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    POSTBACK = "postback"
    VIDEO_PLAY_COMPLETE = "videoPlayComplete"
    BEACON = "beacon"
    ACCOUNT_LINK = "accountLink"
    UNSPECIFIED = "unspecified"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    LOCATION = "location"
    STICKER = "sticker"
    UNSPECIFIED = "unspecified"


class GroupType(str, Enum):
    USER = "user"
    GROUP = "group"
    ROOM = "room"


# ===== Basic Models =====


@dataclass
class DeliveryContext:
    isRedelivery: bool  # :contentReference[oaicite:0]{index=0}


@dataclass
class Emoji:
    index: int
    length: int
    productId: str
    emojiId: str  # :contentReference[oaicite:1]{index=1}


@dataclass
class Mentionee:
    index: int
    length: int
    type: str
    userId: str = None
    isSelf: Optional[bool] = None  # :contentReference[oaicite:2]{index=2}


@dataclass
class Mention:
    mentionees: List[Mentionee]  # :contentReference[oaicite:3]{index=3}


@dataclass
class Source:
    type: GroupType
    groupId: Optional[str] = None
    userId: Optional[str] = None  # :contentReference[oaicite:4]{index=4}


@dataclass
class Message:
    id: str
    type: MessageType
    quoteToken: Optional[str]
    markAsReadToken: Optional[str] = None
    stickerId: Optional[str] = None
    packageId: Optional[str] = None
    stickerResourceType: Optional[str] = None
    keywords: Optional[List[str]] = None
    text: Optional[str] = None
    emojis: Optional[List[Emoji]] = None
    mention: Optional[Mention] = None  # :contentReference[oaicite:5]{index=5}


# ===== Main Event =====


@dataclass
class LINEMessageEvent:
    replyToken: str
    type: EventType
    mode: str
    timestamp: int
    webhookEventId: str
    deliveryContext: DeliveryContext
    message: Message  # :contentReference[oaicite:6]{index=6}
    source: Source = None


@dataclass
class LINEMessagingWebhookEvent:
    destination: str
    events: List[LINEMessageEvent]  # :contentReference[oaicite:7]{index=7}
