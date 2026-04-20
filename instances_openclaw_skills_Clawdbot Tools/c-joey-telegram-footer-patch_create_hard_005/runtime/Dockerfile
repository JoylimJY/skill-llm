FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm bash coreutils findutils grep sed && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --break-system-packages setuptools wheel