FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    gcc \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN pip install markitdown[pptx] Pillow pandas openpyxl defusedxml python-docx
RUN npm install -g pptxgenjs

WORKDIR /workspace