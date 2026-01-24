CREATE DATABASE IF NOT EXISTS feedback_db;
USE feedback_db;

CREATE TABLE IF NOT EXISTS feedback_analysis (
    message_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    feedback_text TEXT NOT NULL,
    sentiment_score VARCHAR(20) NOT NULL,
    feedback_timestamp DATETIME NOT NULL,
    analysis_timestamp DATETIME NOT NULL
);
