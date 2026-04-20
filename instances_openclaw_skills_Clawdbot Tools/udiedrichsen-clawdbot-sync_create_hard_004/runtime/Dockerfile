FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    rsync \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyyaml
