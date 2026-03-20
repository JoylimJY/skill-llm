FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    matplotlib==3.7.2 \
    Pillow==10.0.0 \
    reportlab==4.0.4 \
    numpy==1.24.3 \
    PyPDF2==3.0.1

RUN mkdir -p /workspace/canvas-fonts
RUN wget -O /tmp/fonts.zip https://fonts.google.com/download?family=Inter && \
    unzip -q /tmp/fonts.zip -d /workspace/canvas-fonts/ || true
RUN wget -O /tmp/roboto.zip https://fonts.google.com/download?family=Roboto+Mono && \
    unzip -q /tmp/roboto.zip -d /workspace/canvas-fonts/ || true

WORKDIR /workspace