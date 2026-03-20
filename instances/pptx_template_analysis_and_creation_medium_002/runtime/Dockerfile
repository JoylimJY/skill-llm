FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

RUN pip install --break-system-packages markitdown[pptx] Pillow defusedxml python-pptx-interface python-pptx && \
    npm install -g pptxgenjs react react-dom react-icons sharp

RUN pip install --break-system-packages pptxgen

WORKDIR /workspace