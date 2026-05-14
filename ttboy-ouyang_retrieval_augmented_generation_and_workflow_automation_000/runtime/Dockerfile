FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    chromadb \
    sentence-transformers \
    markdown \
    PyYAML

# Install jasper-recall globally via npm
RUN npm install -g jasper-recall --registry https://registry.npmjs.org || true

# Pre-download the sentence-transformers model to avoid timeout during eval
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || true

WORKDIR /workspace