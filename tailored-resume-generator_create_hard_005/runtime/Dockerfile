FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# No additional dependencies strictly needed since generation and evaluation is in Python

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

CMD ["sleep", "infinity"]