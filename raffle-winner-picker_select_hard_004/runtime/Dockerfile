FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       libffi-dev \
       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pandas openpyxl numpy

WORKDIR /workspace
