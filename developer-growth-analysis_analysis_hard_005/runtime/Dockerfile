FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    requests \
    python-dateutil \
    markdown \
    beautifulsoup4 \
    jsonschema

WORKDIR /workspace