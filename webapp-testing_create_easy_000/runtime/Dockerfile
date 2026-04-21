FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Install nodejs & npm (required by playwright)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and dependencies
RUN pip install -U pip
RUN pip install playwright==1.37.0
RUN playwright install chromium

WORKDIR /workspace

# Copy entrypoint to prevent container from exiting if needed
CMD ["bash"]
