from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
import json
import uuid
from datetime import datetime
import os
import time

app = Flask(__name__)

TOPIC_NAME = "feedback-events"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")


# ======================
# Kafka helpers
# ======================
def wait_for_kafka():
    for attempt in range(10):
        try:
            KafkaAdminClient(bootstrap_servers=KAFKA_BROKER).close()
            print("✅ Kafka ready")
            return
        except NoBrokersAvailable:
            print(f"⏳ Kafka not ready ({attempt + 1}/10)")
            time.sleep(3)
    raise RuntimeError("Kafka not available")


def ensure_topic():
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
    try:
        admin.create_topics(
            [NewTopic(name=TOPIC_NAME, num_partitions=1, replication_factor=1)]
        )
        print(f"📌 Topic '{TOPIC_NAME}' created")
    except TopicAlreadyExistsError:
        pass
    finally:
        admin.close()


def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=3,
    )


# ======================
# Routes
# ======================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["customer_id", "feedback_text", "timestamp"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return jsonify({"error": "Invalid timestamp format"}), 400

    event = {
        "message_id": str(uuid.uuid4()),
        "customer_id": data["customer_id"],
        "feedback_text": data["feedback_text"],
        "feedback_timestamp": data["timestamp"],
    }

    producer = get_producer()
    producer.send(TOPIC_NAME, event)
    producer.flush()
    producer.close()

    return jsonify(
        {"message": "Feedback accepted", "message_id": event["message_id"]}
    ), 202


# ======================
# MAIN (THIS IS CRITICAL)
# ======================
if __name__ == "__main__":
    print("🚀 Starting Flask API...")
    wait_for_kafka()
    ensure_topic()
    app.run(host="0.0.0.0", port=5000)
