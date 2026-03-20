FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install markitdown[pptx] python-pptx Pillow

WORKDIR /workspace