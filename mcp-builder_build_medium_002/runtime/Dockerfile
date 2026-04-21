FROM python:3.11-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all necessary files including requirements.txt
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir mcp httpx pydantic

# Expose port if needed (not strictly necessary for stdio)
EXPOSE 8000

# Default command
CMD ["python", "example_search_mcp.py"]