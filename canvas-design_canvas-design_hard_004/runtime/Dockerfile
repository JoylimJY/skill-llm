FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir \
    anthropic \
    pillow \
    matplotlib \
    numpy \
    reportlab \
    requests

WORKDIR /workspace