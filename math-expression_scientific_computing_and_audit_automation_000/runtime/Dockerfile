FROM debian:12

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    bash \
    coreutils \
    findutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install wolframclient -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Create a mock WolframKernel that simulates real Wolfram Engine behavior
RUN mkdir -p /usr/local/bin

# The mock WolframKernel is created in setup_script