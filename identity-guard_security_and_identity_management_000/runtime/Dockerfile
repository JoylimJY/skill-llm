FROM debian:12-slim

RUN apt-get update -o Acquire::Retries=5 && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    jq \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir --timeout=60 \
    pytest \
    jsonschema