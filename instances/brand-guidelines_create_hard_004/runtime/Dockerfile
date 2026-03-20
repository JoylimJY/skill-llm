FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fontconfig \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Poppins and Lora fonts
RUN mkdir -p /usr/share/fonts/truetype/custom

# Download fonts with proper User-Agent and timeout settings
RUN wget --timeout=30 --tries=3 --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
    -O /tmp/poppins.zip "https://fonts.google.com/download?family=Poppins" || \
    echo "Failed to download Poppins font, continuing without it"

RUN wget --timeout=30 --tries=3 --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
    -O /tmp/lora.zip "https://fonts.google.com/download?family=Lora" || \
    echo "Failed to download Lora font, continuing without it"

# Extract fonts if they were downloaded successfully
RUN if [ -f /tmp/poppins.zip ] && [ -s /tmp/poppins.zip ]; then \
        cd /tmp && unzip -o poppins.zip -d /usr/share/fonts/truetype/custom/ 2>/dev/null || true; \
    fi

RUN if [ -f /tmp/lora.zip ] && [ -s /tmp/lora.zip ]; then \
        cd /tmp && unzip -o lora.zip -d /usr/share/fonts/truetype/custom/ 2>/dev/null || true; \
    fi

RUN fc-cache -f -v

RUN pip install --no-cache-dir --break-system-packages \
    python-pptx==0.6.23 \
    pillow==10.1.0

WORKDIR /workspace