FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies with compatible versions removing the conflicting pydantic pin
RUN pip install --no-cache-dir --break-system-packages "httpx>=0.27" "pydantic>=2.8.0" mcp==1.0.0

CMD ["python3", "example_mcp.py"]