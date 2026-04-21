FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    matplotlib==3.8.0 \
    numpy==1.24.3 \
    pillow==10.0.1 \
    reportlab==4.0.4 \
    fpdf2==2.7.6

WORKDIR /workspace