FROM node:20-slim

# Install python3 and bash utilities for scripts
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv bash unzip && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN npm install -g pnpm

WORKDIR /workspace

# Create virtual environment and install Python dependencies for eval script
RUN python3 -m venv /workspace/venv && \
    /workspace/venv/bin/pip install --no-cache-dir --break-system-packages jsonschema

ENV PNPM_HOME=/workspace/.pnpm
ENV PATH=$PATH:$PNPM_HOME/bin
ENV VIRTUAL_ENV=/workspace/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH

# Default shell
SHELL ["/bin/bash", "-c"]