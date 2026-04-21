FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --break-system-packages --upgrade pip setuptools wheel && pip install --break-system-packages "python-pptx>=0.6.22"
WORKDIR /workspace