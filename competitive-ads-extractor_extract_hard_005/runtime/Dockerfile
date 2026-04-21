FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages "pandas" "pillow==9.5.0"

WORKDIR /workspace

# The eval framework will mount scripts and execute them dynamically