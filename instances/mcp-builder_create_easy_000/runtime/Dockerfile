FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages \
    fastmcp \
    pydantic \
    httpx \
    requests \
    anthropic \
    mcp

COPY . .

# Make setup.sh executable
RUN chmod +x setup.sh

# Fix the script name in setup.sh
RUN sed -i 's/gen_inputs_script/gen_inputs.py/g' setup.sh

CMD ["/bin/bash"]