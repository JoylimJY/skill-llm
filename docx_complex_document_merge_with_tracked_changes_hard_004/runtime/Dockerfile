FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    pandoc \
    libreoffice \
    poppler-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir python-docx

WORKDIR /workspace