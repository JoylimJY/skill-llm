FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    qpdf \
    imagemagick \
    libmagickwand-dev \
    ghostscript \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages \
    pypdf==3.17.0 \
    pdfplumber==0.9.0 \
    reportlab==4.0.4 \
    pytesseract==0.3.10 \
    pdf2image==1.16.3 \
    Pillow==10.1.0 \
    matplotlib==3.8.2 \
    pandas==2.1.4 \
    numpy==1.24.3

WORKDIR /workspace