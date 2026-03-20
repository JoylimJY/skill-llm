FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fontconfig \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-pptx==0.6.21 Pillow==10.0.1

WORKDIR /workspace