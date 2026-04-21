FROM python:3.11-slim

RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr libtesseract-dev libjpeg-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir pdfminer.six Pillow pytesseract pandas reportlab

WORKDIR /workspace

ENV LANG C.UTF-8