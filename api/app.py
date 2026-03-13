import os
import json
import uuid
import time
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
import mysql.connector

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

TOPIC_NAME = "customer_feedback_events"

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

producer = None


def wait_for_kafka():
    for _ in range(10):
        try:
            KafkaAdminClient(bootstrap_servers=KAFKA_BROKER).close()
            return
        except NoBrokersAvailable:
            logger.info("Waiting for Kafka...")
            time.sleep(3)
    raise RuntimeError("Kafka not available")


def ensure_topic():
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
    try:
        admin.create_topics(
            [NewTopic(name=TOPIC_NAME, num_partitions=1, replication_factor=1)]
        )
    except TopicAlreadyExistsError:
        pass
    finally:
        admin.close()


def init_producer():
    global producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=3,
    )


def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
    )


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

    try:
        producer.send(TOPIC_NAME, event)
        logger.info(f"Published event {event['message_id']} to Kafka")
    except Exception as e:
        logger.exception("Kafka publish failed")
        return jsonify({"error": "Kafka publish failed"}), 500

    return jsonify({"message": "Feedback accepted", "message_id": event["message_id"]}), 202


@app.route("/feedback/<message_id>", methods=["GET"])
def get_feedback_by_id(message_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM feedback_analysis WHERE message_id = %s",
            (message_id,),
        )

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return jsonify(result), 200

        return jsonify({"error": "Feedback not found"}), 404

    except Exception:
        logger.exception("Database query failed")
        return jsonify({"error": "Database error"}), 500


@app.route("/feedback", methods=["GET"])
def get_feedback_by_sentiment():
    sentiment = request.args.get("sentiment")

    if not sentiment:
        return jsonify({"error": "sentiment query parameter required"}), 400

    sentiment = sentiment.upper()

    if sentiment not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        return jsonify({"error": "Invalid sentiment filter"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM feedback_analysis WHERE sentiment_score = %s",
            (sentiment,),
        )

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(results), 200

    except Exception:
        logger.exception("Database query failed")
        return jsonify({"error": "Database error"}), 500


if __name__ == "__main__":
    wait_for_kafka()
    ensure_topic()
    init_producer()
    app.run(host="0.0.0.0", port=5000)