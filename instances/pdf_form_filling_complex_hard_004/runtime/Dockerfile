FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    qpdf \
    imagemagick \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pypdf pdfplumber reportlab pdf2image pytesseract pandas pillow

WORKDIR /workspace