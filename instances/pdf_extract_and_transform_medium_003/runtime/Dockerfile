FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN pip install --no-cache-dir \
    pypdf==3.0.1 \
    pdfplumber==0.10.3 \
    reportlab==4.0.7 \
    pandas==2.1.4 \
    openpyxl==3.1.2 \
    matplotlib==3.8.2 \
    numpy==1.26.2

COPY . /workspace/