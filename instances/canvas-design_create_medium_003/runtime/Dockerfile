FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libgirepository1.0-dev \
    pkg-config \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    reportlab==4.0.7 \
    Pillow==10.1.0 \
    PyPDF2==3.0.1 \
    matplotlib==3.8.2 \
    numpy==1.25.2 \
    fonttools==4.47.0

WORKDIR /workspace

COPY . .

RUN mkdir -p canvas-fonts
RUN echo 'font placeholder' > canvas-fonts/font_list.txt