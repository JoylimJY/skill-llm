FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && mkdir -p /usr/share/keyrings \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright --break-system-packages
RUN playwright install chromium

WORKDIR /workspace