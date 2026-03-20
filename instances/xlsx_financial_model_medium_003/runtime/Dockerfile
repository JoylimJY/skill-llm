FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    gcc \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pandas openpyxl xlsxwriter

WORKDIR /workspace

RUN mkdir -p scripts

COPY gen_inputs.py scripts/
COPY setup.sh scripts/