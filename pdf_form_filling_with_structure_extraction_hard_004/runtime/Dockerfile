FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    poppler-utils \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --break-system-packages --no-cache-dir \
    pypdf==4.0.1 \
    pdfplumber==0.10.3 \
    reportlab==4.0.9 \
    Pillow==10.1.0 \
    pdf2image==1.16.3
WORKDIR /workspace