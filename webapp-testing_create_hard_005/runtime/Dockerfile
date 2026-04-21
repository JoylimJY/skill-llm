FROM python:3.11-slim

# Install nodejs and npm for frontend (React)
RUN apt-get update && \
    apt-get install -y curl git build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install playwright dependencies
RUN apt-get update && apt-get install -y \
    wget \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    libgbm1 \
    libxshmfence1 \
    ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir playwright==1.34.0
RUN playwright install chromium

# Install Flask for backend server
RUN pip install --no-cache-dir flask

WORKDIR /workspace

# Expose ports for servers
EXPOSE 3000
EXPOSE 5173

# Entrypoint and command will be run externally
