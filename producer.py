#!/usr/bin/env python3
# producer_kp.py - pure-python Kafka producer using kafka-python

from kafka import KafkaProducer
from faker import Faker
import json
import time
import socket
import sys

fake = Faker()

BOOTSTRAP_SERVERS = ["192.168.56.10:9092"]  # your broker(s)

# Create a JSON serializer for values
def json_serializer(v):
    return json.dumps(v).encode("utf-8")

# Create producer
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=json_serializer,
    key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
    retries=5,            # retries on transient errors
    linger_ms=100,        # small batching delay
    request_timeout_ms=20000,
    max_block_ms=60000    # block up to 60s when broker not available
)

def get_registered_user():
    return {
        "name": fake.name(),
        "address": fake.address(),
        "created_at": fake.date_time().isoformat()
    }

def on_send_success(record_metadata):
    print(f"Message delivered to {record_metadata.topic} [{record_metadata.partition}] @ offset {record_metadata.offset}")

def on_send_error(exc):
    print("Message delivery failed:", repr(exc), file=sys.stderr)

if __name__ == "__main__":
    topic = "registered_user"
    print("Producer starting, connecting to:", BOOTSTRAP_SERVERS)
    try:
        while True:
            registered_user = get_registered_user()
            print("Producing message:", registered_user)

            # send is async — returns a Future
            fut = producer.send(topic, key=registered_user["name"], value=registered_user)
            # add callback
            fut.add_callback(on_send_success)
            fut.add_errback(on_send_error)

            # flush periodically (or call producer.flush() to ensure delivery)
            producer.flush(timeout=10)  # block until messages are delivered (or timeout)
            time.sleep(4)
    except KeyboardInterrupt:
        print("Stopping producer...")
    finally:
        try:
            producer.flush(timeout=10)
        except Exception:
            pass
        producer.close()

