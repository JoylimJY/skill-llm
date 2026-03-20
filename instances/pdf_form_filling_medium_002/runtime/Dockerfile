FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    imagemagick \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    pypdf==3.1.0 \
    pdfplumber==0.10.3 \
    reportlab==4.0.7 \
    pillow==10.1.0 \
    pdf2image==1.16.3 \
    pytesseract==0.3.10 \
    pypdfium2==4.25.0 \
    rlextra

# Create scripts directory
RUN mkdir -p /opt/pdf_skill/scripts/

WORKDIR /workspace