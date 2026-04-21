FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
    Pillow==10.0.0 \
    opencv-python==4.8.0.74 \
    numpy==1.24.3 \
    scipy==1.11.1

WORKDIR /workspace