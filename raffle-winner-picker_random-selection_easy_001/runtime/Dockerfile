FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pandas \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pandas

CMD ["python3"]
