FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    reportlab==4.0.4 \
    pillow==10.0.0 \
    matplotlib==3.7.2 \
    numpy==1.25.2

WORKDIR /workspace