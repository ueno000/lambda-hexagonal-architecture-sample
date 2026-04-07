import boto3
import os
import time
from pprint import pprint

boto3.setup_default_session(
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
    region_name="ap-northeast-1",
)

TABLE_NAME = "LINEMessageProcessor"
ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")

cli_dynamo = boto3.client("dynamodb", endpoint_url=ENDPOINT)
cli_streams = boto3.client("dynamodbstreams", endpoint_url=ENDPOINT)

print("=== describe_table ===", flush=True)
table = cli_dynamo.describe_table(TableName=TABLE_NAME)["Table"]
pprint(table, sort_dicts=False)

stream_spec = table.get("StreamSpecification")
stream_arn = table.get("LatestStreamArn")

print("StreamSpecification:", stream_spec, flush=True)
print("LatestStreamArn:", stream_arn, flush=True)

if not stream_arn:
    raise RuntimeError("LatestStreamArn がありません。テーブルで Stream が有効になっていない可能性が高いです。")

print("=== describe_stream ===", flush=True)
stream_desc = cli_streams.describe_stream(StreamArn=stream_arn)["StreamDescription"]
pprint(stream_desc, sort_dicts=False)

shards = stream_desc.get("Shards", [])
print("shard count:", len(shards), flush=True)

if not shards:
    raise RuntimeError("Shard がありません。Stream が正しく作られていない可能性があります。")

shard = shards[0]
shard_id = shard["ShardId"]

print("=== get_shard_iterator ===", flush=True)
iterator = cli_streams.get_shard_iterator(
    StreamArn=stream_arn,
    ShardId=shard_id,
    ShardIteratorType="TRIM_HORIZON",  # LATEST ではなくまずはこれ
)["ShardIterator"]

print("iterator acquired:", iterator is not None, flush=True)

print("=== polling start ===", flush=True)

i=0

while True:
    resp = cli_streams.get_records(ShardIterator=iterator)
    iterator = resp.get("NextShardIterator")

    print(f"[{i}] records count = {len(resp.get('Records', []))}", flush=True)
    pprint(resp.get("Records", []), sort_dicts=False)

    if not iterator:
        print("NextShardIterator is None", flush=True)
        break

    i += 1
    time.sleep(2)
