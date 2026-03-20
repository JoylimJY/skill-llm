FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    pypdf \
    pdfplumber \
    reportlab \
    pdf2image \
    pytesseract \
    pypdfium2 \
    pandas \
    openpyxl \
    pillow \
    numpy