FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# No additional dependencies needed for this task

WORKDIR /workspace

CMD ["python3"]
