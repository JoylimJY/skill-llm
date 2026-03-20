FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    reportlab==4.0.4 \
    PyPDF2==3.0.1 \
    jsonschema==4.17.3 \
    pydantic==2.5.0

WORKDIR /workspace