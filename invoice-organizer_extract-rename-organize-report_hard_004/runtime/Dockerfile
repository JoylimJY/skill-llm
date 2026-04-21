FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils \
       tesseract-ocr \
       ghostscript \
       libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages pytesseract pdf2image pillow pandas reportlab

ENV LANG C.UTF-8

WORKDIR /app

CMD ["bash"]