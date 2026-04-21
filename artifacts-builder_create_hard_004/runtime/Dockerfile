FROM node:20-slim

# Install python and bash utilities for scripts
RUN apt-get update && apt-get install -y python3 python3-pip bash git curl build-essential && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN npm install -g pnpm

# Set workdir
WORKDIR /workspace

# Ensure scripts directory exists for gen_inputs.py to write the tarball
RUN mkdir -p /workspace/scripts

# Default command sleeps so container stays alive for scripts
CMD ["sleep", "infinity"]