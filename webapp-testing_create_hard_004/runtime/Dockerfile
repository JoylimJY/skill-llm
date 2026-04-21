FROM python:3.11-slim

# Install node and npm
RUN apt-get update && apt-get install -y curl build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install python packages
RUN pip install --no-cache-dir playwright flask

# Install playwright browsers
RUN playwright install chromium

# Set workdir
WORKDIR /app

# Expose ports for backend and frontend
EXPOSE 3000 5173

# Default command is bash shell
CMD ["/bin/bash"]
