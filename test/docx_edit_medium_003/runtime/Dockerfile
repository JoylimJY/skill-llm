FROM python:3.11-slim

# Install dependencies: pandoc for text extraction, LibreOffice for accepting changes,
# Python docx library for analysis in eval script
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       pandoc libreoffice libreoffice-writer fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
RUN pip install python-docx

# Copy scripts will be mounted or created at runtime

WORKDIR /workspace
