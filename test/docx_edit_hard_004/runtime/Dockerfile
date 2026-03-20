FROM python:3.11-slim

# Install nodejs and other dependencies
RUN apt-get update && apt-get install -y curl make gcc g++ libzip-dev git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && pip install --break-system-packages lxml python-docx

# Install LibreOffice headless for conversions (also includes soffice.py dependencies)
RUN apt-get install -y libreoffice-common libreoffice-writer \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy scripts for unpack/pack/validate/comment from the skill
COPY scripts /app/scripts
WORKDIR /app

ENV PYTHONPATH=/app/scripts

# Entrypoint is left blank - eval script calls what it needs