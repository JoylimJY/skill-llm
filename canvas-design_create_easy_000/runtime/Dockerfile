FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*
RUN pip install reportlab pillow matplotlib numpy