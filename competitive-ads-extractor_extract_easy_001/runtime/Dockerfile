FROM python:3.11-slim

# Install any packages needed for scraping, image handling, markdown
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
RUN pip install --no-cache-dir requests markdown

# Set working dir
WORKDIR /workspace

# Default command keeps container alive
CMD ["tail", "-f", "/dev/null"]
