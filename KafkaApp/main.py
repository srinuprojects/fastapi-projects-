from fastapi import FastAPI
from pydantic import BaseModel
from kafka import KafkaProducer
import redis
import json

app = FastAPI()

# Connect to Redis (running on localhost:6379)
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


def get_producer():
    return KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )


class Message(BaseModel):
    topic: str
    content: str


@app.get("/")
def home():
    return {"message": "FastAPI + Kafka + Redis is running!"}


@app.post("/send")
def send_message(msg: Message):
    # Step 1: Check Redis cache first
    # Key format: "msg:<topic>:<content>"
    cache_key = f"msg:{msg.topic}:{msg.content}"
    cached = redis_client.get(cache_key)

    if cached:
        # Found in Redis — return instantly without hitting Kafka
        return {"status": "cached", "topic": msg.topic, "content": msg.content}

    # Step 2: Not in cache — send to Kafka
    producer = get_producer()
    producer.send(msg.topic, value={"content": msg.content})
    producer.flush()
    producer.close()

    # Step 3: Save in Redis cache for 60 seconds
    # Next time same message comes → returned from cache instantly
    redis_client.setex(cache_key, 60, msg.content)

    return {"status": "sent", "topic": msg.topic, "content": msg.content}


@app.get("/messages/{topic}")
def get_messages(topic: str):
    # Read all messages stored in Redis for a topic by consumer
    # Consumer stores messages as a Redis List under key "received:<topic>"
    messages = redis_client.lrange(f"received:{topic}", 0, -1)
    return {"topic": topic, "count": len(messages), "messages": messages}
