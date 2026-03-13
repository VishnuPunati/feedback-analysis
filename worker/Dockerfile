FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA=/usr/local/nltk_data

WORKDIR /app

RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader -d /usr/local/nltk_data vader_lexicon

COPY consumer.py .

CMD ["python", "consumer.py"]