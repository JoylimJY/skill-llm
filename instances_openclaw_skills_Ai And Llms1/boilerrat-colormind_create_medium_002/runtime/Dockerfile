FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    imagemagick \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g npm@10 && \
    npm install -g node@20

RUN python -m pip install --no-cache-dir requests
