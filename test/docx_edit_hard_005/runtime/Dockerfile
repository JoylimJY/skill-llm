FROM python:3.11-slim

# Install system dependencies for LibreOffice headless operation and pandoc
RUN apt-get update && apt-get install -y \
    libreoffice \
    pandoc \
    poppler-utils \
    gcc \
    make \
    unzip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages lxml python-docx

# Copy scripts from the skill (assumed to be mapped or built in testing environment)
# For this task, we rely on scripts/office/unpack.py, pack.py, and comment.py
# We provide implementations inline for simplicity

# Add placeholder scripts/office/unpack.py, pack.py, comment.py here, or assume mounted

WORKDIR /workspace

CMD ["/bin/bash", "-c", "tail -f /dev/null"]