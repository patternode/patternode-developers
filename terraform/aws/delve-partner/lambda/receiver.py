"""Patternode webhook receiver for AWS Lambda (Function URL). Standard library and boto3 only.

Verifies the Standard Webhooks signature against the current and previous secrets, drops a
delivery already seen, puts the event on SQS for your workers, and answers 204 at once.
"""

import base64
import hashlib
import hmac
import json
import os
import time

import boto3

TOLERANCE_S = 300
_sm, _ddb, _sqs = boto3.client("secretsmanager"), boto3.client("dynamodb"), boto3.client("sqs")
_cache = {"at": 0.0, "secrets": []}


def _secrets() -> list[str]:
    if time.time() - _cache["at"] > 300:
        value = json.loads(_sm.get_secret_value(SecretId=os.environ["WEBHOOK_SECRET_ARN"])["SecretString"])
        _cache.update(at=time.time(), secrets=[s for s in (value.get("current"), value.get("previous")) if s])
    return _cache["secrets"]


def _valid(headers: dict, body: bytes) -> bool:
    msg_id, ts, sigs = headers.get("webhook-id"), headers.get("webhook-timestamp"), headers.get("webhook-signature", "")
    if not (msg_id and ts and ts.isdigit()) or abs(time.time() - int(ts)) > TOLERANCE_S:
        return False
    given = [s.partition(",")[2] for s in sigs.split(" ") if s.startswith("v1,")]
    for secret in _secrets():
        key = base64.b64decode(secret.removeprefix("whsec_"))
        expected = base64.b64encode(hmac.new(key, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
        if any(hmac.compare_digest(g, expected) for g in given):
            return True
    return False


def handler(event, _context):
    body = event.get("body") or ""
    body = base64.b64decode(body) if event.get("isBase64Encoded") else body.encode()
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if event.get("requestContext", {}).get("http", {}).get("method") != "POST" or not _valid(headers, body):
        return {"statusCode": 400, "body": "invalid"}
    ttl = int(time.time()) + int(os.environ.get("DEDUPE_TTL_HOURS", "48")) * 3600
    try:
        _ddb.put_item(TableName=os.environ["SEEN_TABLE"],
                      Item={"webhook_id": {"S": headers["webhook-id"]}, "expires_at": {"N": str(ttl)}},
                      ConditionExpression="attribute_not_exists(webhook_id)")
    except _ddb.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 204}
    _sqs.send_message(QueueUrl=os.environ["EVENTS_QUEUE_URL"], MessageBody=body.decode(),
                      MessageAttributes={"webhook_id": {"DataType": "String", "StringValue": headers["webhook-id"]}})
    return {"statusCode": 204}
