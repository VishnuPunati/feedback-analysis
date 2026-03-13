# Event-Driven Customer Feedback Analysis System

## Overview

This project implements an event-driven microservice system for collecting, processing, and analyzing customer feedback using **Flask, Apache Kafka, MySQL, and Docker Compose**.

The system decouples request handling from background processing using Kafka, enabling scalable, reliable, and asynchronous feedback analysis.

The API service receives feedback requests and publishes events to Kafka, while a worker service consumes these events, performs sentiment analysis using NLTK VADER, and stores the results in MySQL.

---

# System Architecture

Client → Flask API → Kafka → Worker → MySQL

1. The client submits feedback through REST API endpoints.
2. The Flask API validates the request and publishes the event to Kafka.
3. Kafka acts as the event broker for asynchronous communication.
4. The worker service consumes events from Kafka.
5. The worker performs sentiment analysis using NLTK VADER.
6. Processed feedback results are stored in MySQL.

---

# Services

## API Service (Flask)

The API service exposes REST endpoints for submitting and retrieving feedback.

Responsibilities:

- Accept feedback requests
- Validate input data
- Publish events to Kafka
- Provide endpoints to query analyzed feedback

---

## Kafka

Kafka acts as the messaging system that enables asynchronous communication between services.

Responsibilities:

- Store feedback events
- Deliver events to the worker service
- Ensure reliable event streaming

---

## Zookeeper

Zookeeper is required by Kafka to manage cluster coordination and configuration.

Responsibilities:

- Broker coordination
- Cluster state management

---

## Worker Service

The worker service consumes feedback events from Kafka and performs sentiment analysis.

Responsibilities:

- Consume Kafka messages
- Perform sentiment analysis using NLTK VADER
- Store processed feedback data in MySQL

---

## MySQL Database

MySQL stores processed feedback records and sentiment analysis results.

Responsibilities:

- Persist analyzed feedback
- Support querying feedback results through API endpoints

---

# Project Structure

feedback-analysis/

api/
    app.py
    Dockerfile
    requirements.txt

worker/
    consumer.py
    Dockerfile
    requirements.txt

db/
    init.sql

tests/

docker-compose.yml
.env.example
README.md

---

# Setup Instructions

## Prerequisites

The following tools must be installed before running the project:

- Docker
- Docker Compose

---

## Clone the Repository

git clone <repository-url>
cd feedback-analysis

---

## Start the System

docker compose up --build

Docker Compose will start the following services:

- Zookeeper
- Kafka
- MySQL
- Flask API
- Worker Service

---

## Verify API Health

Open the following URL in a browser or API tool:

http://localhost:5000/health

Expected response:

{
"status": "ok"
}

---

# API Endpoints

## Health Check

GET /health

Response

{
"status": "ok"
}

---

## Submit Feedback

POST /feedback

Request Body

{
"customer_id": "cust_3001",
"feedback_text": "This system is excellent",
"timestamp": "2026-01-24T07:10:00Z"
}

Response

{
"message": "Feedback accepted",
"message_id": "generated-uuid"
}

Status Code

202 Accepted

---

## Retrieve Feedback by ID

GET /feedback/{message_id}

Example

GET /feedback/123e4567-e89b-12d3-a456-426614174000

Response

{
"message_id": "...",
"customer_id": "...",
"feedback_text": "...",
"sentiment_score": "POSITIVE",
"feedback_timestamp": "...",
"analysis_timestamp": "..."
}

---

## Filter Feedback by Sentiment

GET /feedback?sentiment=positive
GET /feedback?sentiment=negative
GET /feedback?sentiment=neutral

Example

GET /feedback?sentiment=positive

Response

Returns all feedback records with the specified sentiment classification.

---

# Sentiment Analysis

The system performs sentiment analysis using **NLTK VADER (Valence Aware Dictionary and sEntiment Reasoner)**.

VADER is a rule-based sentiment analysis tool designed specifically for social media and short text.

Classification rules:

compound ≥ 0.05 → POSITIVE
compound ≤ -0.05 → NEGATIVE
otherwise → NEUTRAL

---

# Database Schema

Feedback results are stored in the **feedback_analysis** table.

Columns:

message_id
customer_id
feedback_text
sentiment_score
feedback_timestamp
analysis_timestamp

The **message_id** column acts as the primary key, ensuring idempotent processing and preventing duplicate inserts.

---

# Design Decisions

## Event-Driven Architecture

Kafka enables asynchronous processing by decoupling request handling from background processing.

Benefits include:

- Improved scalability
- Increased system resilience
- Independent service deployment

---

## Idempotent Processing

Each feedback event contains a unique message ID that is stored as the primary key in the database. This prevents duplicate processing if the same event is consumed multiple times.

---

## Service Isolation

API and Worker services are separated so that each component can scale independently depending on workload.

---

## Containerized Deployment

Docker containers ensure consistent environments across development and production.

Docker Compose orchestrates all services including Kafka, Zookeeper, MySQL, API, and Worker.

---

## Environment Configuration

Environment variables are used to configure services such as:

- Kafka broker address
- MySQL credentials
- Database name

This allows flexible configuration across environments.

---

# Failure Handling

The system includes several reliability mechanisms:

Kafka ensures reliable message delivery.

Worker services safely ignore duplicate messages.

MySQL transactions guarantee consistent data storage.

Docker restart policies automatically recover failed containers.

---

# Developer Details

Name: Vishnu Varun Punati
Roll Number: 22MH1A4259
Department: CSE – Artificial Intelligence and Machine Learning
