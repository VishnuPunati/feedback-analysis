import json
import time
import os
import logging
from datetime import datetime
from kafka import KafkaConsumer
import mysql.connector
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
TOPIC_NAME = "customer_feedback_events"

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> str:
    score = analyzer.polarity_scores(text)
    if score["compound"] >= 0.05:
        return "POSITIVE"
    if score["compound"] <= -0.05:
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
            logger.info("MySQL connected")
            return
        except Exception:
            logger.info("Waiting for MySQL...")
            time.sleep(5)


def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
    )


wait_for_mysql()
db = get_db_connection()
cursor = db.cursor()

consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="sentiment_analyzer_group",
)

logger.info("Kafka worker started")

for message in consumer:
    try:
        event = message.value

        sentiment = analyze_sentiment(event["feedback_text"])

        analysis_time = datetime.utcnow()

        feedback_time = datetime.strptime(
            event["feedback_timestamp"],
            "%Y-%m-%dT%H:%M:%SZ"
        )

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
        logger.info(f"Processed message {event['message_id']} sentiment={sentiment}")

    except mysql.connector.errors.IntegrityError:
        logger.warning("Duplicate message skipped")

    except mysql.connector.errors.InterfaceError:
        logger.warning("MySQL connection lost, reconnecting")
        db = get_db_connection()
        cursor = db.cursor()

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")