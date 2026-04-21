FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN pip install --no-cache-dir --break-system-packages jsonschema

WORKDIR /app

CMD ["bash"]