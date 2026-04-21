FROM python:3.11-slim

# Install dependencies for PDF and image text extraction
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies including fpdf
RUN pip install --no-cache-dir pytesseract pdf2image pillow pandas fpdf

# Set working directory
WORKDIR /workspace

# Entrypoint will be mounted dynamically, do not COPY any scripts