import boto3
import json
from app.config import settings

sqs = boto3.client(
    "sqs",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)

def poll_messages(max_messages: int = 10) -> list[dict]:
    response = sqs.receive_message(
        QueueUrl=settings.sqs_queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=5,
    )

    messages = response.get("Messages", [])
    parsed = []

    for message in messages:
        body = json.loads(message["Body"])
        receipt_handle = message["ReceiptHandle"]

        sqs.delete_message(
            QueueUrl=settings.sqs_queue_url,
            ReceiptHandle=receipt_handle,
        )

        parsed.append(body)

    return parsed