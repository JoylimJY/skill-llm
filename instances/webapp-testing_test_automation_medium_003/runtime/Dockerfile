FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and dependencies
RUN python3 -m pip install --break-system-packages playwright==1.40.0
RUN python3 -m playwright install chromium
RUN python3 -m playwright install-deps

# Install Node.js dependencies globally for the test app
RUN npm install -g create-react-app

WORKDIR /workspace