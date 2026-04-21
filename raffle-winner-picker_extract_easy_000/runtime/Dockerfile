FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
 && rm -rf /var/lib/apt/lists/*

RUN pip install pandas numpy

ENV LANG=C.UTF-8
