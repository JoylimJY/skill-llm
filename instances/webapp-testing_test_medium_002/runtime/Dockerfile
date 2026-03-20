FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies using apt instead of deprecated apt-key
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install Python packages with --break-system-packages flag
RUN pip3 install --break-system-packages playwright==1.40.0
RUN playwright install chromium

# Create dummy package files for initial build
RUN echo '{"name": "todo-app", "version": "0.1.0", "private": true, "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0", "react-scripts": "5.0.1"}, "scripts": {"start": "react-scripts start", "build": "react-scripts build", "test": "react-scripts test", "eject": "react-scripts eject"}}' > package.json
RUN echo '{"name": "todo-app", "version": "0.1.0", "lockfileVersion": 2, "requires": true, "packages": {}}' > package-lock.json

# Install Node.js dependencies
RUN npm install

COPY . .
RUN npm run build