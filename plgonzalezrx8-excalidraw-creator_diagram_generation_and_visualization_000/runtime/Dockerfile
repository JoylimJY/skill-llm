FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install the excalidraw renderer dependencies
WORKDIR /opt/excalidraw-creator/scripts
RUN npm install --save \
    @excalidraw/excalidraw \
    canvas \
    jsdom \
    || true

# Try alternative renderer package
RUN npm install -g rough || true

WORKDIR /workspace