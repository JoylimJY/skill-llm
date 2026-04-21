FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DOCKER_BUILDKIT=1
ENV BUILDKIT_INLINE_CACHE=1