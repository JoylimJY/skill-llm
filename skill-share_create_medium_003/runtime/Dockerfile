FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    zip \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pyyaml \
    requests \
    jsonschema \
    slack-sdk

WORKDIR /workspace