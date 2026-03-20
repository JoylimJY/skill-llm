FROM node:20-slim

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm

WORKDIR /workspace

COPY . .

RUN if [ -f requirements.txt ]; then pip3 install -r requirements.txt --break-system-packages; fi

ENV PATH=/workspace/scripts:$PATH