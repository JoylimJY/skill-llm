FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-liberation \
    fonts-dejavu \
    fonts-noto \
    ghostscript \
    poppler-utils \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    matplotlib==3.7.2 \
    numpy==1.24.3 \
    pillow==10.0.0 \
    reportlab==4.0.4 \
    pypdf==3.12.2 \
    pdf2image==1.16.3

WORKDIR /workspace