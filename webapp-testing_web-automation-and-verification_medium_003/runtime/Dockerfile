FROM node:20-slim

# Install Python and Playwright system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    libgbm1 \
    libxshmfence1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages playwright pytest
RUN playwright install chromium
WORKDIR /workspace
