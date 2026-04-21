FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --break-system-packages --no-cache-dir markdown2==2.4.9
WORKDIR /workspace