from kafka import KafkaConsumer
import redis
import json

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Connect to Kafka and subscribe to "my-topic"
consumer = KafkaConsumer(
    "my-topic",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="my-group"
)

print("Listening for messages on 'my-topic'... (Press Ctrl+C to stop)")

for message in consumer:
    value = message.value

    # Store every received message in Redis as a List
    # Key: "received:my-topic"  → List of all messages
    redis_client.lpush(f"received:{message.topic}", json.dumps(value))

    print(f"Received → topic: {message.topic} | value: {value}")
    print(f"Saved to Redis key: received:{message.topic}")
