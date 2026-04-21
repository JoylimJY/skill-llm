FROM python:3.11-slim
RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-eng libgl1 libsm6 libxext6 libxrender1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytesseract pdf2image Pillow fpdf