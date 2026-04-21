FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y poppler-utils tesseract-ocr \
    libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev libharfbuzz-dev libfribidi-dev libxcb1-dev && \
    pip install --no-cache-dir --break-system-packages pdfplumber Pillow pytesseract==0.3.10 reportlab && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace