FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for MCP Inspector
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages \
    mcp \
    pydantic \
    httpx \
    pytest \
    anthropic \
    lxml \
    beautifulsoup4 \
    requests

# Install MCP Inspector
RUN npm install -g @modelcontextprotocol/inspector

COPY . .

# Make setup.sh executable and create gen_inputs_script symlink
RUN chmod +x setup.sh && \
    ln -s gen_inputs.py gen_inputs_script && \
    touch eval_script && chmod +x eval_script

CMD ["/bin/bash"]