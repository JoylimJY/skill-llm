FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN pip install --no-cache-dir \
    pypdf \
    pdfplumber \
    reportlab \
    pandas \
    openpyxl \
    matplotlib \
    numpy

COPY . /workspace/