import json
import time
import os
from datetime import datetime
from kafka import KafkaConsumer
import mysql.connector

# ======================
# Config
# ======================
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC_NAME = "feedback-events"

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root_password")
MYSQL_DB = os.getenv("MYSQL_DB", "feedback_db")

POSITIVE_WORDS = ["good", "great", "excellent", "amazing", "awesome", "helpful"]
NEGATIVE_WORDS = ["bad", "poor", "terrible", "worst", "slow", "hate"]

# ======================
# Helpers
# ======================
def analyze_sentiment(text: str) -> str:
    text = text.lower()
    if any(word in text for word in POSITIVE_WORDS):
        return "POSITIVE"
    if any(word in text for word in NEGATIVE_WORDS):
        return "NEGATIVE"
    return "NEUTRAL"


def wait_for_mysql():
    while True:
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
            )
            conn.close()
            print("✅ MySQL connected")
            return
        except Exception:
            print("⏳ Waiting for MySQL...")
            time.sleep(5)


def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
    )


# ======================
# Startup
# ======================
wait_for_mysql()
db = get_db_connection()
cursor = db.cursor()

consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="feedback-analysis-group",
)

print("🚀 Kafka Worker started...")

# ======================
# Consume loop
# ======================
for message in consumer:
    event = message.value

    sentiment = analyze_sentiment(event["feedback_text"])
    analysis_time = datetime.utcnow()

    # ✅ Convert ISO → MySQL-safe DATETIME
    feedback_time = datetime.strptime(
        event["feedback_timestamp"],
        "%Y-%m-%dT%H:%M:%SZ"
    )

    try:
        cursor.execute(
            """
            INSERT INTO feedback_analysis
            (message_id, customer_id, feedback_text, sentiment_score,
             feedback_timestamp, analysis_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                event["message_id"],
                event["customer_id"],
                event["feedback_text"],
                sentiment,
                feedback_time,
                analysis_time,
            ),
        )
        db.commit()
        print(f"✅ Stored feedback {event['message_id']} [{sentiment}]")

    except mysql.connector.errors.IntegrityError:
        print(f"⚠️ Duplicate skipped: {event['message_id']}")

    except mysql.connector.errors.InterfaceError:
        print("🔄 MySQL reconnecting...")
        db = get_db_connection()
        cursor = db.cursor()
