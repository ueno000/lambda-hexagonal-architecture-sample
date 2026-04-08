import os
import time
import logging
from pprint import pformat

import boto3
from boto3.dynamodb.types import TypeDeserializer
from app.application.line.reply_message import reply_message
from app.domain.model.line.line_message_processor import LINEMessageProcessor

TABLE_NAME = "LINEMessageProcessor"
ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
REGION = "ap-northeast-1"
POLL_INTERVAL_SECONDS = 2
SHARD_ITERATOR_TYPE = "TRIM_HORIZON"  # 運用で監視開始後だけ見たいなら LATEST

deserializer = TypeDeserializer()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_clients():
    boto3.setup_default_session(
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
        region_name=REGION,
    )

    dynamo = boto3.client("dynamodb", endpoint_url=ENDPOINT)
    streams = boto3.client("dynamodbstreams", endpoint_url=ENDPOINT)
    return dynamo, streams


def get_stream_arn(dynamo_client, table_name: str) -> str:
    table = dynamo_client.describe_table(TableName=table_name)["Table"]

    logger.info("table stream specification: %s", table.get("StreamSpecification"))
    logger.info("table latest stream arn: %s", table.get("LatestStreamArn"))

    stream_arn = table.get("LatestStreamArn")
    if not stream_arn:
        raise RuntimeError(
            f"LatestStreamArn がありません。table={table_name} で Stream が有効でない可能性があります。"
        )

    return stream_arn


def get_first_shard_id(streams_client, stream_arn: str) -> str:
    stream_desc = streams_client.describe_stream(StreamArn=stream_arn)["StreamDescription"]
    shards = stream_desc.get("Shards", [])

    logger.info("stream status: %s", stream_desc.get("StreamStatus"))
    logger.info("shard count: %s", len(shards))

    if not shards:
        raise RuntimeError("Shard がありません。Stream が正しく作られていない可能性があります。")

    return shards[0]["ShardId"]


def get_shard_iterator(streams_client, stream_arn: str, shard_id: str) -> str:
    iterator = streams_client.get_shard_iterator(
        StreamArn=stream_arn,
        ShardId=shard_id,
        ShardIteratorType=SHARD_ITERATOR_TYPE,
    )["ShardIterator"]

    if not iterator:
        raise RuntimeError("ShardIterator の取得に失敗しました。")

    logger.info("iterator acquired: shard_id=%s", shard_id)
    return iterator


def deserialize_image(image):
    if not image:
        return None
    return {k: deserializer.deserialize(v) for k, v in image.items()}


def process_record(record: dict) -> None:
    event_name = record.get("eventName")
    dynamodb = record.get("dynamodb", {})

    keys = deserialize_image(dynamodb.get("Keys"))
    new_image = deserialize_image(dynamodb.get("NewImage"))
    old_image = deserialize_image(dynamodb.get("OldImage"))

    logger.info("eventName=%s", event_name)
    logger.info("keys=%s", pformat(keys))
    logger.info("new_image=%s", pformat(new_image))
    logger.info("old_image=%s", pformat(old_image))

    # ここに業務処理を書く

    if not new_image:
        return

    reply_message(
        line_message_processor_status=LINEMessageProcessor.parse_obj(new_image).processing_status,
        reply_token=keys.get("id"),
    )


def handle_stream_records(records: list[dict]) -> None:
    for record in records:
        try:
            process_record(record)
        except Exception:
            logger.exception("record processing failed: %s", pformat(record))


def poll_once(streams_client, iterator: str) -> tuple[str | None, list[dict]]:
    response = streams_client.get_records(ShardIterator=iterator)
    next_iterator = response.get("NextShardIterator")
    records = response.get("Records", [])
    return next_iterator, records


def run() -> None:
    dynamo_client, streams_client = create_clients()

    stream_arn = get_stream_arn(dynamo_client, TABLE_NAME)
    shard_id = get_first_shard_id(streams_client, stream_arn)
    iterator = get_shard_iterator(streams_client, stream_arn, shard_id)

    poll_count = 0
    logger.info("polling start")

    while True:
        iterator, records = poll_once(streams_client, iterator)

        logger.info("[%s] records count = %s", poll_count, len(records))

        if records:
            handle_stream_records(records)

        if not iterator:
            logger.warning("NextShardIterator is None. polling stopped.")
            break

        poll_count += 1
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
