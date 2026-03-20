FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libreoffice \
    poppler-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pptxgenjs react react-dom sharp react-icons

RUN pip3 install --break-system-packages markitdown[pptx] Pillow defusedxml

WORKDIR /workspace