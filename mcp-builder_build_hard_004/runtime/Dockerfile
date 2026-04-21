FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy setup script with correct name
COPY setup.sh ./

RUN chmod +x setup.sh && ./setup.sh

# Expose port for optional HTTP transport if needed
EXPOSE 8000

# The server and scripts will be mounted dynamically into /app at runtime
CMD ["python3"]