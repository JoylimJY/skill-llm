FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir \
    pillow \
    reportlab \
    matplotlib \
    numpy

WORKDIR /workspace