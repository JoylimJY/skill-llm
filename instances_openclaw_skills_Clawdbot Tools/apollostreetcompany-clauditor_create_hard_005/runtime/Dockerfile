FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    cargo \
    systemd \
    sudo \
    ca-certificates \
    build-essential \
    pkg-config \
    libssl-dev \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest