import time

from kafka import KafkaProducer
import json

# Step 1: Connect to Kafka (running locally on port 9092)
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")  # Convert dict → JSON bytes
)

# Step 2: Send a message to a topic called "my-topic"
message = {"name": "Srinu", "action": "learning Kafka"}

for _ in range(5):  # Send the same message 5 times
    message["timestamp"] = str(int(time.time()))  # Add a timestamp to make each message unique
    producer.send("my-topic", value=message)
    producer.flush()  # Make sure the message is actually sent

print(f"Message sent: {message}")

producer.close()
