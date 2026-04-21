FROM python:3.11-slim

# Install Node.js (needed to run npm commands for frontend and backend)
RUN apt-get update && apt-get install -y curl git build-essential && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Install Playwright system dependencies (required for Chromium)
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    libgbm1 \
    libxshmfence1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and Python dependencies
RUN pip install --no-cache-dir playwright --break-system-packages
RUN playwright install chromium

# Also install backend dependencies (express, cors) for node backend
RUN npm install -g concurrently

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /workspace

COPY gen_inputs.py ./gen_inputs.py

# Fix the typo in the file before running it
RUN sed -i 's/eos\.makedirs/os.makedirs/g' gen_inputs.py

RUN python gen_inputs.py