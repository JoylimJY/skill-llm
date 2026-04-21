FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir \
    matplotlib \
    numpy \
    reportlab \
    Pillow \
    fpdf2

WORKDIR /workspace