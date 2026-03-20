FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install Playwright
RUN pip install --break-system-packages playwright flask flask-cors requests
RUN playwright install chromium
RUN playwright install-deps chromium

# Install frontend dependencies globally to avoid permission issues
RUN npm install -g create-react-app serve

WORKDIR /workspace
COPY . .

# Install project dependencies after copying files
RUN if [ -f "frontend/package.json" ]; then cd frontend && npm install; fi