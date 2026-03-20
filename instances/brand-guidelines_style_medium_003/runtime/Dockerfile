FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-pptx==0.6.23 Pillow==10.0.0

WORKDIR /workspace