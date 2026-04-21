FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# No additional packages needed for this task

WORKDIR /app

CMD ["sleep", "infinity"]
