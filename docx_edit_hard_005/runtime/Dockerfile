FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    pandoc \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages python-docx lxml beautifulsoup4

WORKDIR /workspace