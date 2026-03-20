FROM node:20-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g create-react-app typescript

RUN pip3 install --break-system-packages requests beautifulsoup4 lxml selenium

WORKDIR /workspace