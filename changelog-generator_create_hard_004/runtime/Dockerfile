FROM python:3.11-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies if any (e.g., pygit2 or equivalent)
RUN pip install --no-cache-dir pygit2

# Set working directory
WORKDIR /workspace

CMD ["bash"]
