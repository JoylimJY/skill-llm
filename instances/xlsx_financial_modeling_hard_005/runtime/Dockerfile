FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    gcc \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pandas openpyxl xlsxwriter numpy

WORKDIR /workspace