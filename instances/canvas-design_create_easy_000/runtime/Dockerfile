FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    reportlab==4.0.4 \
    pillow==10.0.0 \
    matplotlib==3.7.2 \
    numpy==1.24.3 \
    pypdf2==3.0.1

WORKDIR /workspace