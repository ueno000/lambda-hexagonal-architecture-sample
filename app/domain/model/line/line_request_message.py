from dataclasses import dataclass, asdict
from typing import List, Any


@dataclass
class RequestReplyMessage:
    # Webhookで受信する応答トークン
    replyToken: str
    # 送信するメッセージ（最大5件）
    messages: List[Any]


@dataclass
class TextMessage:
    type: str
    text: str


@dataclass
class ImageMessage:
    type: str
    originalContentUrl: str
    previewImageUrl: str


@dataclass
class VideoMessage:
    type: str
    originalContentUrl: str
    previewImageUrl: str


@dataclass
class AudioMessage:
    type: str
    originalContentUrl: str
    duration: str


@dataclass
class FlexMessage:
    type: str
    altText: str
    contents: Any


# JSON化の例
if __name__ == "__main__":
    msg = RequestReplyMessage(
        replyToken="token123",
        messages=[
            asdict(TextMessage(type="text", text="Hello"))
        ]
    )

    import json
    print(json.dumps(asdict(msg), ensure_ascii=False))
