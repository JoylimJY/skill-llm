FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pypdf2 \
    pytesseract \
    pillow \
    pdf2image \
    pdfplumber \
    fpdf2

WORKDIR /workspace
COPY . .
RUN if [ -f setup_script.sh ]; then chmod +x setup_script.sh && ./setup_script.sh; fi