FROM python:3.11-slim

# Install git for commit history
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Configure git user for commits
RUN git config --global user.email "you@example.com" && \
    git config --global user.name "Your Name"

# Install any python packages needed for evaluation
RUN pip install --no-cache-dir pyyaml

WORKDIR /app