FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir python-docx lxml