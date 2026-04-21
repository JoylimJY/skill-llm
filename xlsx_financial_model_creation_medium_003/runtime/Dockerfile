FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    gcc \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages pandas openpyxl xlsxwriter

WORKDIR /workspace