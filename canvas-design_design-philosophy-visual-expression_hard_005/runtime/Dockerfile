FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --break-system-packages reportlab pillow matplotlib numpy