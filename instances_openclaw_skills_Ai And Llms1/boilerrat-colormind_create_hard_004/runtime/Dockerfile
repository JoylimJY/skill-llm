FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates curl && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --no-cache-dir --break-system-packages requests