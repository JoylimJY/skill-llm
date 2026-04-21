FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-lxml \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g docx

WORKDIR /workspace
