FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Install fonts
RUN mkdir -p /usr/share/fonts/truetype/custom
WORKDIR /tmp

# Install Poppins font
RUN wget -q https://fonts.google.com/download?family=Poppins -O poppins.zip && \
    unzip -q poppins.zip -d poppins && \
    cp poppins/*.ttf /usr/share/fonts/truetype/custom/ || true

# Install Lora font
RUN wget -q https://fonts.google.com/download?family=Lora -O lora.zip && \
    unzip -q lora.zip -d lora && \
    cp lora/*.ttf /usr/share/fonts/truetype/custom/ || true

RUN fc-cache -f -v

WORKDIR /workspace

RUN pip install python-pptx