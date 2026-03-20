FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    unzip \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Install Google Fonts from GitHub releases
RUN mkdir -p /usr/share/fonts/truetype/poppins && \
    mkdir -p /usr/share/fonts/truetype/lora && \
    apt-get update && apt-get install -y curl && \
    curl -L -o poppins.zip 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf' && \
    curl -L -o /usr/share/fonts/truetype/poppins/Poppins-Regular.ttf 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf' && \
    curl -L -o /usr/share/fonts/truetype/poppins/Poppins-Bold.ttf 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf' && \
    curl -L -o /usr/share/fonts/truetype/lora/Lora-Regular.ttf 'https://github.com/google/fonts/raw/main/ofl/lora/Lora-Regular.ttf' && \
    curl -L -o /usr/share/fonts/truetype/lora/Lora-Bold.ttf 'https://github.com/google/fonts/raw/main/ofl/lora/Lora-Bold.ttf' && \
    fc-cache -fv && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* poppins.zip

RUN pip install --no-cache-dir --break-system-packages \
    python-pptx==0.6.21 \
    pillow==10.0.0 \
    openpyxl==3.1.2

WORKDIR /workspace