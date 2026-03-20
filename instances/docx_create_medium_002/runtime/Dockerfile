FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    pandoc \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g docx

WORKDIR /workspace

COPY . .

RUN python3 -m pip install --no-cache-dir --break-system-packages lxml beautifulsoup4