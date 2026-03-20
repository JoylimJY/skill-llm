FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN pip install --break-system-packages playwright flask requests beautifulsoup4

RUN npm install -g express cors body-parser axios

RUN playwright install chromium

WORKDIR /workspace

COPY . .

RUN if [ -f "setup_script.sh" ]; then chmod +x setup_script.sh && ./setup_script.sh; fi