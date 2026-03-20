FROM node:20-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g typescript tsx

COPY gen_inputs.py gen_inputs_script
RUN python3 gen_inputs_script

RUN npm install

CMD ["/bin/bash"]