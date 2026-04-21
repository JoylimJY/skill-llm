FROM python:3.11-slim

# Install dependencies needed to handle pptx and pdf
RUN apt-get update && apt-get install -y \
    poppler-utils \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

RUN pip install --no-cache-dir --break-system-packages python-pptx PyPDF2 reportlab

WORKDIR /app