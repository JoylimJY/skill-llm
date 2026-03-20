FROM node:20-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for evaluation
RUN pip3 install --no-cache-dir --break-system-packages \
    anthropic==0.39.0 \
    httpx==0.27.2 \
    pydantic==2.9.2 \
    python-dotenv==1.0.1

# Install Node.js packages that might be needed
RUN npm install -g typescript tsx

# Copy and run input generation script first
COPY gen_inputs.py ./
RUN python3 gen_inputs.py

# Copy package files and install dependencies
RUN npm install

# Copy source files
COPY . .

# Build the project
RUN npm run build || true