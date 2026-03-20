FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for MCP server and evaluation
RUN pip install --no-cache-dir \
    mcp==1.1.0 \
    pydantic==2.10.4 \
    httpx==0.28.1 \
    fastapi==0.115.6 \
    anthropic==0.39.0

# Copy and run input generation
COPY gen_inputs.py gen_inputs_script.py
RUN python gen_inputs_script.py

# Create a placeholder evaluation script
RUN echo '#!/usr/bin/env python3\nprint("Evaluation script placeholder")' > eval_script.py

CMD ["/bin/bash"]