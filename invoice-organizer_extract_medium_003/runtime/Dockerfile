FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    imagemagick \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pdf2image pytesseract pillow pandas fpdf

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1

# The framework mounts the code and gen_inputs scripts dynamically