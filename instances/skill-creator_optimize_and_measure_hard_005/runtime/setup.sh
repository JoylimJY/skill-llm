#!/bin/bash
set -e

echo "Setting up performance optimization environment..."

# Make sure all Python packages are available
pip install --no-cache-dir \
    flask-caching==2.0.2 \
    redis==4.6.0 \
    flask-limiter==3.5.0

echo "Environment setup complete"