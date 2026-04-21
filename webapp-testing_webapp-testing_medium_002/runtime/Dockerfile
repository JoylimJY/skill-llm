FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages playwright && python -m playwright install chromium && python -m playwright install-deps chromium

WORKDIR /workspace
