FROM node:20-slim

RUN apt-get update && apt-get install -y python3 python3-pip \
    && npm install -g docx \
    && pip3 install --no-cache-dir --break-system-packages python-docx

WORKDIR /workspace