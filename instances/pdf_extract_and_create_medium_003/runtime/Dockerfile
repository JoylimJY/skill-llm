FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    pypdf \
    pdfplumber \
    reportlab \
    pandas \
    Pillow