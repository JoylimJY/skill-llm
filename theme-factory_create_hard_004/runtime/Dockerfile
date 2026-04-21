FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fonts-dejavu-core fonts-roboto \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN pip install --no-cache-dir --break-system-packages markdown==3.4.4 jinja2==3.1.2

WORKDIR /workspace

ENV LANG C.UTF-8