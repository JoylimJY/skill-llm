FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir \
    reportlab \
    pyyaml \
    jsonschema