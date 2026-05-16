FROM python:3.11-slim

RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir numpy==1.26.4 && \
    pip install --no-cache-dir pandas==2.2.2 && \
    pip install --no-cache-dir ta==0.11.0 && \
    pip install --no-cache-dir pytest==8.2.2

WORKDIR /workspace