FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pptxgenjs

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --break-system-packages --no-cache-dir "markitdown[pptx]" python-pptx

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /workspace
