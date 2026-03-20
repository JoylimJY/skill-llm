FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    anthropic==0.40.0 \
    python-docx==1.1.2 \
    pandas==2.2.0 \
    pypdf==4.0.1 \
    python-dateutil==2.8.2 \
    openpyxl==3.1.2 \
    fpdf2==2.7.6

WORKDIR /workspace

COPY gen_inputs.py gen_inputs_script.py
COPY setup.sh .

RUN chmod +x setup.sh