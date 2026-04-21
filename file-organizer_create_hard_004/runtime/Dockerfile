FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pillow python-docx

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
