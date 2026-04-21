FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages numpy markdown Pillow

WORKDIR /workspace

CMD ["bash"]