FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --break-system-packages \
    python-pptx==0.6.21 \
    pillow==10.0.0 \
    requests==2.31.0 \
    pdfplumber==0.9.0 \
    reportlab==4.0.4
WORKDIR /app