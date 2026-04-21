FROM python:3.11-slim

# Install nodejs and npm to run frontend
RUN apt-get update \
    && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs build-essential git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# Set working directory
WORKDIR /app

# Install python dependencies
RUN pip install --no-cache-dir playwright

# Install Playwright browsers
RUN playwright install chromium

# Install npm dependencies after gen_inputs.py creates package.json

# Default shell
SHELL ["/bin/bash", "-c"]

# Entrypoint is interactive shell (task scripts run dynamically)
CMD ["bash"]
