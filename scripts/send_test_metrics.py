import boto3
import json
import random
import time
from dotenv import load_dotenv
import os

load_dotenv()

sqs = boto3.client(
    "sqs",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

QUEUE_URL = os.getenv("SQS_QUEUE_URL")

servers = [
    {"name": "web-server-01", "cpu": 23, "memory": 41},
    {"name": "db-server-01", "cpu": 78, "memory": 86},
    {"name": "cache-01", "cpu": 95, "memory": 60},
    {"name": "api-server-02", "cpu": 45, "memory": 72},
]

for server in servers:
    message = {
        "server_name": server["name"],
        "cpu_percent": server["cpu"],
        "memory_percent": server["memory"],
    }

    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message),
    )

    print(f"Sent: {server['name']} — CPU {server['cpu']}% | Memory {server['memory']}%")

print("\nAll messages sent to SQS.")