FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    pandoc \
    libreoffice \
    poppler-utils \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g docx

RUN python3 -m pip install --break-system-packages python-docx

WORKDIR /workspace