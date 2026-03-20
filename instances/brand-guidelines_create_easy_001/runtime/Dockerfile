FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-pptx==0.6.21

WORKDIR /workspace