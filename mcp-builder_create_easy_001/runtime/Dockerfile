FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir httpx pydantic mcp

# The server.py and other scripts will be mounted dynamically

CMD ["python", "server.py"]
