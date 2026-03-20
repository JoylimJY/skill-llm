FROM node:20-slim

# Install python3 and pip for eval script
RUN apt-get update && apt-get install -y python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install npm docx package globally
RUN npm install -g docx

# Install Python package for eval script
RUN pip3 install --break-system-packages python-docx

WORKDIR /workspace

COPY gen_inputs.py ./
COPY setup.sh ./

RUN bash setup.sh